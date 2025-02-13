import pandas as pd
from scipy.signal import butter, sosfiltfilt

from utils import filter_files

def load_dataset(
        task: str = 'all',
        split: str = 'both',
        exclude: list = None,
        include: list = None,
        folder: str = None
) -> tuple | list:
    """
    Function to load the EEG Eye-Tracking Dataset according to specifications.

    :param task: String specifying which task to load. Either of:
        - "level-1-smooth": Loads data from level-1 smooth experiment.
        - "level-1-saccades": Loads data from level-1 saccades experiment.
        - "level-2-smooth": Loads data from level-1 smooth experiment.
        - "level-2-saccades": Loads data from level-2 saccades experiment.
        - "level-1": Loads data from all level-1 experiments.
        - "level-2": Loads data from all level-2 experiments.
        - "smooth": Loads data from all smooth experiments.
        - "saccades": Loads data from all saccades experiments.
        - "all": Loads data from all experiments (default).
    :param split: String specifying which subset to load. Either of:
        - "train": Loads training data.
        - "test": Loads test data.
        - "both": Loads training and test data.
    :param exclude: List of recordings to exclude, given in the format
        "PXXX_YY", where XXX denotes the participant number and YY the session
        number.
    :param include: List of recordings to exclude, given in the format
        "PXXX_YY", where XXX denotes the participant number and YY the session
        number.
    :param folder: Path to folder containing the data. If None (Default), the
        data is fetched and managed with pooch.
    :return: Returns a list of Pandas DataFrames, if 'split' in ['train',
        'test'], and a tuple of both lists, if 'split' == 'both'.
    """
    if folder is None:
        from utils import fetch_data
        files = fetch_data(
            task=task,
            split=split,
            exclude=exclude,
            include=include
        )
    else:
        import os

        available_files = [os.path.join(root, fp)
                           for root, _, fps in os.walk(folder) for fp in fps]
        files = filter_files(
            available_files,
            task=task,
            split=split,
            exclude=exclude,
            include=include
        )

    if isinstance(files, list):
        return [pd.read_csv(fp) for fp in files]
    elif isinstance(files, tuple):
        return tuple([pd.read_csv(fp) for fp in fps] for fps in files)
    else:
        raise ValueError(f'Files should be a list or tuple.')


def filter_recording(
        recording: pd.DataFrame,
        notch_50: bool = True,
        notch_60: bool = True,
        bandpass: bool = True,
        fs: int = 256,
        Q: int = 30,
        bandpass_order: int = 5
) -> pd.DataFrame:
    """
    Function to filter EEG data from a recording given as Pandas DataFrame.

    :param recording: Recording containing EEG data.
    :param notch_50: Boolean specifying whether to apply 50 Hz notch filter.
    :param notch_60: Boolean specifying whether to apply 60 Hz notch filter.
    :param bandpass: Boolean specifying whether to apply bandpass filter
        between 0.5 and 40 Hz.
    :param fs: Sample frequency of EEG data. Defaults to 256 Hz.
    :param Q: Quality factor of notch filters. Defaults to 30.
    :param bandpass_order: Order of bandpass filter. Defaults to 5.
    :return:
    """
    eeg_columns = [col for col in recording.columns if 'EEG' in col]

    nyq = 0.5 * fs  # Nyquist frequency
    f0 = 50 / nyq
    f1 = 60 / nyq
    low = 0.5 / nyq
    high = 40 / nyq

    filters = [
        (notch_50, 2, [f0 - 1 / Q, f0 + 1 / Q], 'bandstop'),
        (notch_60, 2, [f1 - 1 / Q, f1 + 1 / Q], 'bandstop'),
        (bandpass, bandpass_order, [low, high], 'bandpass')
    ]

    recording_filtered = recording.copy()

    for col in eeg_columns:
        data = recording_filtered[col]

        for apply_filter, order, freqs, filter_type in filters:
            if apply_filter:
                sos = butter(order, freqs, btype=filter_type, output="sos")
                data = sosfiltfilt(sos, data)

        recording_filtered[col] = data

    return recording_filtered


if __name__ == '__main__':
    import matplotlib.pyplot as plt

    task = 'level-1-saccades'
    split = 'train'

    recordings = load_dataset(task=task, split=split, include=['P001_01'])
    rec_src = recordings[0]

    eeg_columns = [col for col in rec_src.columns if 'EEG' in col]
    rec_filtered = filter_recording(rec_src)

    fig, axes = plt.subplots(4)

    for ax, col in zip(axes, eeg_columns):
        ax.plot(rec_src['EEG_TP9'].iloc[:512], label='Original')
        ax.plot(rec_filtered['EEG_TP9'].iloc[:512], label='Filtered')
        ax.legend()
        ax.set_ylabel(col)

    plt.show()
