import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import ccf

from load_data import load_dataset

def calculate_correlations(recordings: list) -> dict:
    """
    Calculate lag with maximal cross-correlation between gaze and stimulus,
    for 'x' and 'y' coordinates separately.

    :param recordings: List of recordings (as Pandas DataFrame).
    :return: Dictionary of lags with maximal correlation for 'x' and 'y' axis.
    """
    correlations = {'x': [], 'y': []}

    for df in recordings:
        for cord in ['x', 'y']:
            corr = _calculate_ccf(
                df[f'Gaze_{cord}'].to_numpy(),
                df[f'Stimulus_{cord}'].to_numpy()
            )
            max_corr = np.argmax(corr) - 256
            correlations[cord].append(max_corr)

    return correlations

def visualize_ccf(recording: pd.DataFrame, coord: str = 'x'):
    """
    Visualize the cross-correlation function of the gaze and stimulus and the
    given recording.

    :param recording: Recording containing stimulus and gaze data.
    :param coord: Coordinate of the gaze and stimulus. Default is 'x'.
    """
    corr = _calculate_ccf(
        recording[f'Gaze_{coord}'].to_numpy(),
        recording[f'Stimulus_{coord}'].to_numpy()
    )

    plt.plot(np.arange(-256, 512) / 256, corr)
    plt.scatter([np.argmax(corr) / 256 - 1], [np.max(corr)], c='tab:orange', s=20)
    plt.xlabel('Lag (in s)')
    plt.ylabel('Cross-Correlation')
    plt.show()


def _calculate_ccf(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    """
    Auxiliary function to calculate cross-correlation function of two time series.

    :param x: First time series, as NumPy array.
    :param y: Second time series, as NumPy array.
    :return: Cross-correlation function, as NumPy array.
    """
    corr = ccf(x, y, adjusted=False, nlags=512)
    corr_inv = ccf(y, x, adjusted=False, nlags=256)[::-1]
    corr = np.concatenate((corr_inv, corr))

    return corr


if __name__ == '__main__':
    # Visualize a single cross-correlation function
    recording = load_dataset()[0][0]
    visualize_ccf(recording)

    # Calculate maximal lag of cross-correlation function for all files
    for task in ['1-saccades', '1-smooth', '2-saccades', '2-smooth']:
        recordings = load_dataset(task=task)
        recordings_flat = recordings[0] + recordings[1]
        corr = calculate_correlations(recordings_flat)

        print(f"Average lag between gaze and stimulus for {task} experiments.")
        for k, v in corr.items():
            print(k, np.mean(v), np.std(v))
