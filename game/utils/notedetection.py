import numpy as np
import librosa
import time


def merge_vocal_background_with_padding(vocal_onset, vocal_duration, background_onset, background_duration, tempo, precision=1.0):
    spb = 60 / tempo * precision
    merge_onset = []
    merge_duration = []
    merge_label = []

    l1 = vocal_onset.shape[0]
    l2 = background_onset.shape[0]
    i = j = k = 0

    while i < l1 and j < l2:
        if vocal_onset[i] <= background_onset[j]:
            chosen_onset = vocal_onset[i]
            chosen_duration = vocal_duration[i]
            label = 1
            i += 1
        else:
            chosen_onset = background_onset[j]
            chosen_duration = background_duration[j]
            label = 0
            j += 1

        merge_onset.append(chosen_onset)
        merge_duration.append(chosen_duration)
        merge_label.append(label)

        k += 1
        if False and k > 1 and merge_label[-2] == 1 and merge_label[-1] == 1:
            count = 0
            blank_start = merge_onset[-2] + merge_duration[-2]
            while merge_onset[-1] - blank_start - count * spb >= spb:
                merge_onset.append(blank_start + count * spb)
                count += 1
                k += 1

    while i < l1:
        merge_onset.append(vocal_onset[i])
        merge_duration.append(vocal_duration[i])
        merge_label.append(1)
        i += 1

    while j < l2:
        merge_onset.append(background_onset[j])
        merge_duration.append(background_duration[j])
        merge_label.append(0)
        j += 1

    return merge_onset, merge_duration, merge_label

def vocal_separation(y, sr):
    pre_time = time.time()
    # And compute the spectrogram magnitude and phase
    S_full, phase = librosa.magphase(librosa.stft(y))
    cur_time = time.time()
    print(cur_time - pre_time)
    pre_time = cur_time

    # Play back a 5-second excerpt with vocals
    # Audio(data=y[10 * sr:15 * sr], rate=sr)

    # S_filter = librosa.decompose.nn_filter(S_full,
    #                                        aggregate=np.median,
    #                                        metric='cosine',
    #                                        width=int(librosa.time_to_frames(2, sr=sr)))
    #
    # S_filter = np.minimum(S_full, S_filter)

    # We'll compare frames using cosine similarity, and aggregate similar frames
    # by taking their (per-frequency) median value.
    #
    # To avoid being biased by local continuity, we constrain similar frames to be
    # separated by at least 2 seconds.
    #
    # This suppresses sparse/non-repetetitive deviations from the average spectrum,
    # and works well to discard vocal elements.

    S_filter = librosa.decompose.nn_filter(S_full,
                                           aggregate=np.median,
                                           metric='cosine',
                                           width=int(librosa.time_to_frames(3.0, sr=sr)))
    cur_time = time.time()
    print(cur_time - pre_time)
    pre_time = cur_time
    # The output of the filter shouldn't be greater than the input
    # if we assume signals are additive.  Taking the pointwise minimum
    # with the input spectrum forces this.
    S_filter = np.minimum(S_full, S_filter)

    # We can also use a margin to reduce bleed between the vocals and instrumentation masks.
    # Note: the margins need not be equal for foreground and background separation
    # adjust 1
    # noisy: 2, 10
    # clean: 10, 28
    margin_i, margin_v = 10, 20
    power = 3

    mask_i = librosa.util.softmask(S_filter,
                                   margin_i * (S_full - S_filter),
                                   power=power)

    mask_v = librosa.util.softmask(S_full - S_filter,
                                   margin_v * S_filter,
                                   power=power)
    cur_time = time.time()
    print(cur_time - pre_time)
    pre_time = cur_time

    # Once we have the masks, simply multiply them with the input spectrum
    # to separate the components

    S_foreground = mask_v * S_full
    S_background = mask_i * S_full
    cur_time = time.time()
    print(cur_time - pre_time)
    pre_time = cur_time

    y_foreground = librosa.istft(S_foreground * phase)
    y_background = librosa.istft(S_background * phase)

    cur_time = time.time()
    print(cur_time - pre_time)
    pre_time = cur_time

    return y_foreground, y_background

def load_audio(filename):
    x, fs = librosa.load(filename)
    return x, fs


def onset_roundings(onset_times, onset_durations, tempo, precision=0.25):
    spb = 60 / tempo * precision
    onset_times = np.around(onset_times / spb, decimals=0) * spb
    onset_durations = np.around(onset_durations / spb, decimals=0) * spb
    onset_durations = np.clip(onset_durations, spb, 99999)
    return onset_times, onset_durations


def onset_paddings(onset_times, onset_durations, tempo, abs_x, precisions=1.0, sr=22050):
    spb = 60 / tempo * precisions
    local_range = 100
    onset_samples = librosa.time_to_samples(onset_times, sr=sr)

    length = len(onset_times)
    i = 0
    while i < length - 1:
        interval_samples = np.arange(-local_range, local_range).reshape(1, -1) + onset_samples[i]
        pre_amplitude = abs_x[interval_samples].reshape(-1, 2 * local_range)
        pre_amplitude = np.max(pre_amplitude, axis=1)
        count = 0
        # print(i, onset_times.shape, length)
        while onset_times[i + 1] - onset_times[i] - onset_durations[i] - count * spb > spb:
            new_start_time = onset_times[i] + onset_durations[i] + count * spb
            new_onset_sample = librosa.time_to_samples(new_start_time, sr=sr)

            interval_samples = np.arange(-local_range, local_range).reshape(1, -1) + new_onset_sample
            cur_amplitude = abs_x[interval_samples].reshape(-1, 2 * local_range)
            cur_amplitude = np.max(cur_amplitude, axis=1)

            if cur_amplitude >= pre_amplitude / 2:
                i += 1
                length += 1
                onset_times = np.insert(onset_times, i, new_start_time, axis=0)
                onset_durations = np.insert(onset_durations, i, spb, axis=0)
                onset_samples = np.insert(onset_samples, i, new_onset_sample, axis=0)
                count = 0
            else:
                count += 1

        i += 1
    return onset_times, onset_durations


def onset_detection(x, fs, fft_length=1024, fft_hop_length=512):
    x_foreground, x_background = vocal_separation(x, fs)
    onset_list = []
    duration_list = []
    # adjust 2
    for x, fs in zip([x_foreground, x_background], [fs, fs]):

        y = abs(librosa.stft(x, n_fft=fft_length, hop_length=fft_hop_length, center=False))
        onset_env = librosa.onset.onset_strength(y=x, sr=fs)
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=fs)
        print('tempo:', tempo)

        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=fs)
        # using onset_detect from librosa to detect onsets (using parameters delta=0.04, wait=4)
        onset_times = librosa.frames_to_time(onset_frames, sr=fs)
        onset_samples = librosa.frames_to_samples(onset_frames)
        onset_durations = onset_length_detection(x, y, onset_samples, sr=fs)
        print('before:', np.max(onset_durations))
        onset_times, onset_durations = onset_roundings(onset_times, onset_durations, tempo)
        # onset_times, onset_durations = onset_paddings(onset_times, onset_durations, tempo, np.abs(x), sr=fs)

        onset_list.append(onset_times)
        duration_list.append(onset_durations)

    # onset_times, onset_durations, onset_labels = merge_vocal_background_with_padding(onset_list[0], duration_list[0], onset_list[1], duration_list[1], tempo)
    onset_times, onset_durations = onset_list[0], duration_list[0]
    print('after:', np.max(onset_durations))
    return onset_times, onset_durations


def onset_detection_back(x, fs, fft_length=1024, fft_hop_length=512):
    y = abs(librosa.stft(x, n_fft=fft_length, hop_length=fft_hop_length, center=False))
    onset_env = librosa.onset.onset_strength(y=x, sr=fs)
    tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=fs)

    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=fs)
    # using onset_detect from librosa to detect onsets (using parameters delta=0.04, wait=4)
    onset_times = librosa.frames_to_time(onset_frames, sr=fs)
    onset_samples = librosa.frames_to_samples(onset_frames)
    onset_durations = onset_length_detection(x, y, onset_samples, sr=fs)

    onset_times, onset_durations = onset_roundings(onset_times, onset_durations, tempo)
    onset_times, onset_durations = onset_paddings(onset_times, onset_durations, tempo, np.abs(x), sr=fs)
    return onset_times, onset_durations


# detect length of each onsets
def onset_length_detection(x, y, onset_samples, fft_length=1024, fft_hop_length=512, sr=22050, tolerance=1):
    residual_size = fft_length - fft_hop_length
    filtered_onset_samples = onset_samples
    filtered_onset_samples[onset_samples < fft_length] = fft_length - residual_size
    onset_frame_indices = (filtered_onset_samples - fft_length) // residual_size + 1

    onset_frame = y[:, onset_frame_indices]
    peaks = np.argmax(onset_frame, axis=0)
    #     print('amplitude: ', np.max(onset_frame, axis=0))
    abs_x = np.abs(x)
    x_size = abs_x.shape
    tindex = np.arange(20) + onset_frame_indices[2]
    tmax = np.argmax(y[:, tindex], axis=0)

    length_sum = np.ones((onset_samples.shape[0]))
    valid_mask = np.ones((onset_samples.shape[0])).astype(bool)

    old_peaks = np.argmax(onset_frame, axis=0)
    old_amplitude = np.max(onset_frame, axis=0)

    local_range = 100
    interval_samples = np.arange(-local_range, local_range).reshape(1, -1) + onset_samples.reshape(-1, 1)
    interval_samples = np.clip(interval_samples, 0, x_size)
    standard_amplitude = abs_x[interval_samples].reshape(-1, 2 * local_range)
    standard_amplitude = np.max(standard_amplitude, axis=1)

    temp_indices = onset_frame_indices + 1
    temp_onset_samples = onset_samples + residual_size

    old_frame = onset_frame

    number_of_frames = y.shape[1]
    while valid_mask.sum() > 0:
        new_onset_frame = y[:, temp_indices]
        new_peaks = np.argmax(new_onset_frame, axis=0)
        new_amplitude = np.max(new_onset_frame, axis=0)

        diff = np.mean((old_frame - new_onset_frame) ** 2, axis=0)

        satisfaction = np.ones((onset_samples.shape[0]))

        # compute distribution difference
        # satisfaction = np.logical_and(satisfaction, diff > 0.5)
        # print(np.min(diff))
        satisfaction = np.logical_and(satisfaction, diff < 1e-3)

        # check change in max frequency peak
        # satisfaction = np.logical_and(satisfaction, np.abs(new_peaks - old_peaks) <= tolerance)

        # use max frequency amplitude
        # satisfaction = np.logical_and(satisfaction, new_amplitude >= old_amplitude / 2)

        # use fix overall amplitude
        interval_samples = np.arange(-local_range, local_range).reshape(1, -1) + temp_onset_samples.reshape(-1, 1)
        cur_amplitude = abs_x[interval_samples].reshape(-1, 2 * local_range)
        cur_amplitude = np.max(cur_amplitude, axis=1)
        mask2 = (standard_amplitude - cur_amplitude <= standard_amplitude * 0.8)
        # satisfaction = np.logical_and(satisfaction, mask2)

        valid_mask = np.logical_and(valid_mask, satisfaction)
        length_sum += valid_mask

        old_peaks = new_peaks
        old_frame = new_onset_frame
        temp_indices += 1
        temp_onset_samples += residual_size
        satisfaction = temp_indices < number_of_frames
        valid_mask = np.logical_and(valid_mask, satisfaction)

        temp_indices[~satisfaction] = number_of_frames - 1
        temp_onset_samples[~satisfaction] = 0

    durations = length_sum * residual_size / sr
    print('max durations:', np.max(durations))
    return durations


def process_audio(filename):
    x, fs = load_audio(filename)
    return onset_detection(x, fs)
