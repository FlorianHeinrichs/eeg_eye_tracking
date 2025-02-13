from pathlib import Path
import warnings
from pmdarima.arima import StepwiseContext
from pmdarima.arima import auto_arima
from tqdm import tqdm
import numpy as np
import pandas as pd
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "input_dir",
    metavar="input-dir",
    help="Path to the directory with csv files that contain missing values",
)
parser.add_argument(
    "output_dir",
    metavar="output-dir",
    help="Path to the directory where resulting csv files will be saved.",
)
parser.add_argument(
    "--overwrite",
    help="Whether to overwrite the existing files.",
    action="store_true",
)
args = parser.parse_args()

input_dir = Path(args.input_dir)
output_dir = Path(args.output_dir)
overwrite = args.overwrite

for csv_file in (pbar := tqdm(list(input_dir.glob("*.csv")))):
    pbar.set_description(f"Processing {csv_file.name}")

    output_file = output_dir / csv_file.name

    if output_file.exists() and not overwrite:
        continue

    df = pd.read_csv(csv_file)
    eeg_columns = [col for col in df.columns if 'EEG' in col]

    for electrode in (
        pbar2 := tqdm(eeg_columns, leave=False)
    ):
        values = df[electrode].to_numpy()

        # Step 1: Find the missing values
        # Problem: Missing values are zeros, which in some cases are valid values
        # Solution: Uninterrupted sequences of at least three zeros (which are
        #           unlikely to be valid) are considered missing values

        zeros = 1 * (values == 0)
        consecutive_zeros = np.zeros_like(zeros)
        consecutive_zeros[0] = zeros[0]

        for i in range(1, len(zeros)):
            if zeros[i] == 1:
                consecutive_zeros[i] = consecutive_zeros[i - 1] + 1
            else:
                consecutive_zeros[i] = 0

        # Go over consecutive_zeros backwards and mark sections with more than 3 zeros
        missing = np.zeros_like(consecutive_zeros)
        count = 0
        for i in range(len(consecutive_zeros)-1, -1, -1):
            if consecutive_zeros[i] >= 3:
                count = consecutive_zeros[i]
            missing[i] = count > 0
            count -= 1

        if not np.any(missing):
            continue

        # Step 2: Impute the missing values
        # The timeseries is modeled as an SARIMA process for which the ar, ma,
        # and seasonal orders are automatically determined.
        # A "Kalman smoother" is then used to impute the missing values taking
        # into account past and future values.
        # Also see: https://github.com/statsmodels/statsmodels/issues/2551#issuecomment-408735647
        # and https://github.com/statsmodels/statsmodels/issues/2551#issuecomment-482814921
        try:
            pbar2.set_description(
                f"Imputing missing values for {electrode} (determining model)"
            )

            with warnings.catch_warnings():
                # When auto_arima does not finish within the time limit, it
                # raises a UserWarning
                warnings.simplefilter("ignore")

                # Limit the maximum duration of the fitting process to 30 seconds
                # For further optimization, see: https://alkaline-ml.com/pmdarima/tips_and_tricks.html#using-stepwisecontext
                with StepwiseContext(max_dur=30):
                    model = auto_arima(
                        values[1000:3000],
                        seasonal=True,
                        m=5,
                        maxiter=10,
                        suppress_warnings=True,
                    )

            pbar2.set_description(
                f"Imputing missing values for {electrode} (fitting model)"
            )

            values[missing] = np.nan
            model_fit = model.fit(values).arima_res_

            df[electrode] = model_fit.filter_results.smoothed_forecasts[0, :]
        except Exception as e:
            print(f"Failed to impute missing values for {electrode} in "
                  f"{csv_file.name}")
            print(e)

    df.to_csv(output_file, index=False)
