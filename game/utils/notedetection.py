import numpy as np
import librosa
import time
import copy

def merge_close_onset(onset_times, onset_durations, tempo, precision=0.125):
    spb = 60 / tempo * precision
    i = 0
    l = len(onset_times)
    while i < l-1:
        if abs(onset_times[i+1] - onset_times[i]) <= precision:
            onset_durations[i] = max(onset_times[i] + onset_durations[i], onset_times[i+1] + onset_durations[i+1]) - onset_times[i]
            onset_times = np.delete(onset_times, i+1)
            onset_durations = np.delete(onset_durations, i+1)
            l -= 1
        else:
            i += 1
    return onset_times, onset_durations


def remove_noisy_onset(onset_times, onset_durations, x, sr):
    onset_index = librosa.time_to_samples(onset_times, sr=sr)
    onset_index_range = onset_index.reshape(-1, 1) + np.arange(0, 200)
    onset_sample_range = x[onset_index_range]
    onset_amplitude = np.sqrt(np.mean(onset_sample_range**2, axis=1))

    mean_amplitude = np.mean(onset_amplitude)

    valid_samples = onset_amplitude > mean_amplitude / 12
    onset_times = onset_times[valid_samples]
    onset_durations = onset_durations[valid_samples]

    return onset_times, onset_durations

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
    # And compute the spectrogram magnitude and phase
    S_full, phase = librosa.magphase(librosa.stft(y))

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
                                           width=int(librosa.time_to_frames(2.0, sr=sr)))

    # The output of the filter shouldn't be greater than the input
    # if we assume signals are additive.  Taking the pointwise minimum
    # with the input spectrum forces this.
    S_filter = np.minimum(S_full, S_filter)

    # We can also use a margin to reduce bleed between the vocals and instrumentation masks.
    # Note: the margins need not be equal for foreground and background separation
    # adjust 1
    # noisy: 2, 10
    # clean: 10, 28

    margin_i, margin_v = 5, 20
    power = 2

    filter_mean = np.max(S_filter)
    unfilter_mean = np.max(S_full - S_filter)

    mask_i = librosa.util.softmask(S_filter,
                                   margin_i * (S_full - S_filter),
                                   power=power)

    mask_v = librosa.util.softmask(S_full - S_filter,
                                   margin_v * S_filter,
                                   power=power)

    # Once we have the masks, simply multiply them with the input spectrum
    # to separate the components

    S_foreground = mask_v * S_full
    S_background = mask_i * S_full

    y_foreground = librosa.istft(S_foreground * phase)
    y_background = librosa.istft(S_background * phase)


    return y_foreground, y_background

def load_audio(filename):
    x, fs = librosa.load(filename)
    return x, fs


def onset_roundings(onset_times, onset_durations, tempo, precision=0.125):
    spb = 60 / tempo * precision
    phase_shifts = np.linspace(0, spb, num=60)  # Generate a range of phase shifts

    best_alignment = None
    best_error = float('inf')

    for phase_shift in phase_shifts:
        aligned_onset_times = np.around((onset_times - phase_shift) / spb, decimals=0) * spb + phase_shift
        alignment_error = np.sum(np.cbrt(np.abs(aligned_onset_times - onset_times)))
        # cube root is used to decrease the effect of outliers

        if alignment_error < best_error:
            aligned_onset_durations = np.around(np.array(onset_durations) / spb, decimals=0) * spb
            valid_mask = aligned_onset_durations > 0
            best_alignment = (np.array(aligned_onset_times), np.array(aligned_onset_durations))
            best_error = alignment_error
    return best_alignment


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


def onset_detection(x, fs, fft_length=1024, fft_hop_length=512, tempo=None):
    x_foreground, x_background = vocal_separation(copy.deepcopy(x), fs)
    onset_list = []
    duration_list = []
    onset_bars_list = []

    # adjust 2
    onset_env = librosa.onset.onset_strength(y=x, sr=fs)
    if tempo is None:
        tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=fs)
        tempo = np.around(tempo, 0)

    print('tempo:', tempo)
    print('frame rate:', fs)
    x_background = x
    for x in [x_foreground, x_background]:

        y = abs(librosa.stft(x, n_fft=fft_length, hop_length=fft_hop_length, center=False))
        S = librosa.feature.melspectrogram(y=x, sr=fs, n_fft=fft_length, hop_length=fft_hop_length)
        onset_env = librosa.onset.onset_strength(y=x, sr=fs)

        onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=fs)
        # using onset_detect from librosa to detect onsets (using parameters delta=0.04, wait=4)
        onset_times = librosa.frames_to_time(onset_frames, sr=fs)
        onset_samples = librosa.frames_to_samples(onset_frames)
        onset_durations = onset_length_detection(x, y, onset_samples, sr=fs)

        onset_times, onset_durations = remove_noisy_onset(onset_times, onset_durations, x, sr=fs)
        onset_times, onset_durations = merge_close_onset(onset_times, onset_durations, tempo)

        onset_times, onset_durations = onset_roundings(onset_times, onset_durations, tempo)
        # onset_times, onset_durations = onset_paddings(onset_times, onset_durations, tempo, np.abs(x), sr=fs)

        onset_list.append(onset_times)
        duration_list.append(onset_durations)

    # calculate the bar number for each onset
    beats_per_bar = 8   # usually it's 4 beats per bar, but having 8 beats per pattern makes a more enjoyable map
    bar_duration = 60 / tempo * beats_per_bar
    onset_bars_list = [(i // bar_duration + 1) for i in onset_list]
    print('durations:', duration_list[0])
    # onset_times, onset_durations, onset_labels = merge_vocal_background_with_padding(onset_list[0], duration_list[0], onset_list[1], duration_list[1], tempo)
    onset_times, onset_durations, onset_bars_list = onset_list[0], duration_list[0], onset_bars_list[0]
    return onset_times, onset_durations, onset_bars_list, tempo


def onset_detection_back(x, fs, fft_length=1024, fft_hop_length=512, tempo=None):
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
    return onset_times, onset_durations, [], tempo


# detect length of each onsets
def onset_length_detection(x, y, onset_samples, fft_length=1024, fft_hop_length=512, sr=22050, tolerance=4):
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

    number_of_frames = y.shape[1]

    temp_indices = onset_frame_indices + 1
    temp_onset_samples = onset_samples + residual_size
    satisfaction = temp_indices < number_of_frames
    valid_mask = np.logical_and(valid_mask, satisfaction)

    temp_indices[~satisfaction] = number_of_frames - 1
    temp_onset_samples[~satisfaction] = 0

    old_frame = onset_frame

    while valid_mask.sum() > 0:
        new_onset_frame = y[:, temp_indices]
        new_peaks = np.argmax(new_onset_frame, axis=0)
        new_amplitude = np.max(new_onset_frame, axis=0)

        diff = np.mean((old_frame - new_onset_frame) ** 2, axis=0)

        satisfaction = np.ones((onset_samples.shape[0]))

        # compute distribution difference
        satisfaction = np.logical_and(satisfaction, diff < 6)

        # check change in max frequency peak
        satisfaction = np.logical_and(satisfaction, np.abs(new_peaks - old_peaks) <= tolerance)

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
    # print('max durations:', np.max(durations))
    # print('min durations:', np.min(durations))
    return durations


def process_audio(filename, tempo=None):
    x, fs = load_audio(filename)
    return onset_detection(x, fs, tempo=tempo)
