import numpy as np
import librosa


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
    while i < length-1:
        interval_samples = np.arange(-local_range, local_range).reshape(1, -1) + onset_samples[i]
        pre_amplitude = abs_x[interval_samples].reshape(-1, 2 * local_range)
        pre_amplitude = np.max(pre_amplitude, axis=1)
        count = 0
        # print(i, onset_times.shape, length)
        while onset_times[i+1] - onset_times[i] - onset_durations[i] - count * spb > spb:
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
    y = abs(librosa.stft(x, n_fft=fft_length, hop_length=fft_hop_length, center=False))
    onset_env = librosa.onset.onset_strength(y=x, sr=fs)
    tempo = librosa.beat.tempo(onset_envelope=onset_env, sr=fs)
    print('tempo:', tempo)

    onset_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=fs)
    # using onset_detect from librosa to detect onsets (using parameters delta=0.04, wait=4)
    onset_times = librosa.frames_to_time(onset_frames, sr=fs)
    onset_samples = librosa.frames_to_samples(onset_frames)
    onset_durations = onset_length_detection(x, y, onset_samples, sr=fs)

    onset_times, onset_durations = onset_roundings(onset_times, onset_durations, tempo)
    onset_times, onset_durations = onset_paddings(onset_times, onset_durations, tempo, np.abs(x), sr=fs)
    return onset_times, onset_durations


# detect length of each onsets
def onset_length_detection(x, y, onset_samples, fft_length=1024, fft_hop_length=512, sr=22050, tolerance=3):
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
        satisfaction = np.logical_and(satisfaction, diff < 1.2)


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
    return length_sum * residual_size / sr


def process_audio(filename):
    x, fs = load_audio(filename)
    return onset_detection(x, fs)