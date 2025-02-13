import os
from pathlib import Path
import csv
import sys
import pyxdf
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser()
parser.add_argument(
    "xdf_dir",
    metavar="xdf-dir",
    help="The path to the directory containing the xdf files that will be converted.",
)
parser.add_argument(
    "csv_dir",
    metavar="csv-dir",
    help="The path to the directory where the resulting csv files will be saved.",
)
args = parser.parse_args()

input_dir = Path(args.xdf_dir)
output_dir = Path(args.csv_dir)

def get_stream(xdf, content_type):
    return next(
        (stream for stream in xdf["data"] if stream["info"]["type"] == [content_type]),
        None,
    )

# Find all files in the specified directory
for filename in tqdm(os.listdir(input_dir)):
    if not filename.endswith(".xdf"):
        continue

    # load xdf
    data, header = pyxdf.load_xdf(input_dir / filename)
    xdf = {"data": data, "header": header}

    # Get all streams from the xdf file
    eeg_stream = get_stream(xdf, "EEG")
    gaze_stream = get_stream(xdf, "Gaze")
    stimulus_stream = get_stream(xdf, "Stimulus")
    marker_stream = get_stream(xdf, "Markers")

    # Create maps from channel labels to original channel positions
    eeg_channel_i = {
        channel["label"][0]: i
        for i, channel in enumerate(
            eeg_stream["info"]["desc"][0]["channels"][0]["channel"]
        )
    }
    gaze_channel_i = {
        channel["label"][0]: i
        for i, channel in enumerate(
            gaze_stream["info"]["desc"][0]["channels"][0]["channel"]
        )
    }
    stimulus_channel_i = {
        channel["label"][0]: i
        for i, channel in enumerate(
            stimulus_stream["info"]["desc"][0]["channels"][0]["channel"]
        )
    }

    # Get metadata from the stimulus stream
    # This metadata is used to convert the stimulus and gaze x and y values from pixels to mm
    desc = stimulus_stream["info"]["desc"][0]
    setup = desc["setup"][0]
    display = setup["display"][0]
    resolution_primary = {
        key: float(value[0]) for key, value in display["resolution_primary"][0].items()
    }
    canvas = {key: float(value[0]) for key, value in display["canvas"][0].items()}
    # settings = setup["experiment"][0]["settings"][0] # Not needed for px to mm conversion

    metadata = {"resolution_primary": resolution_primary, "canvas": canvas}

    def px_to_mm(px, dpi, center):
        # dpi = canvas.width * 25.4 / canvas.widthMM
        # mm = px * (widthMM / width) = px * (25.4 / dpi)
        return (px - center) * (25.4 / dpi)

    def px_to_mm_x(px):
        return px_to_mm(
            px,
            metadata["resolution_primary"]["x_dpi"],
            metadata["canvas"]["x"] + metadata["canvas"]["width"] / 2,
        )

    def px_to_mm_y(px):
        return px_to_mm(
            px,
            metadata["resolution_primary"]["y_dpi"],
            metadata["canvas"]["y"] + metadata["canvas"]["height"] / 2,
        )

    # Create iterators for all streams
    eeg_data = zip(eeg_stream["time_series"], eeg_stream["time_stamps"])
    gaze_data = zip(gaze_stream["time_series"], gaze_stream["time_stamps"])
    stimulus_data = zip(stimulus_stream["time_series"], stimulus_stream["time_stamps"])
    marker_data = zip(marker_stream["time_series"], marker_stream["time_stamps"])

    # Find the "Start" marker
    # The presentation starts when the state transitions from "starting" to "moving"
    start_marker_types, start_marker_timestamp = next(marker_data)
    if start_marker_types[0] != "starting":
        # raise ValueError(f"No 'Start' marker found in file {filename}")
        print(f"No 'Start' marker found in file {filename}", file=sys.stderr)
        continue
    start_marker_types, start_marker_timestamp = next(marker_data)
    if start_marker_types[0] != "moving":
        # raise ValueError(f"Invalid 'Start' marker in file {filename}")
        print(f"Invalid 'Start' marker in file {filename}", file=sys.stderr)
        continue

    # Skip the eeg measurements that happened before the "Start" marker
    while next(eeg_data)[1] < start_marker_timestamp:
        pass
        # Note: by not saving the first element that does not match the while
        # clause we are loosing one element but that is negligible

    # Open a new csv file to which we write to
    new_filename = filename.removesuffix(".xdf") + ".csv"
    with open(output_dir / new_filename, "w", newline="\n") as fo:
        writer = csv.writer(fo)

        # Write csv header
        header = [
            "Timestamp",
            "EEG_TP9",
            "EEG_AF7",
            "EEG_AF8",
            "EEG_TP10",
            "Gaze_x",
            "Gaze_y",
            "Stimulus_x",
            "Stimulus_y",
        ]
        writer.writerow(header)

        next_gaze_data = next(gaze_data)
        next_stimulus_data = next(stimulus_data)
        next_marker_data = next(marker_data)

        # Initialize state, gaze and stimulus
        state = "moving"  # Possible states: stopped, starting, pre_moving, moving
        gaze_x, gaze_y = None, None
        stimulus_x, stimulus_y = None, None

        first_timestamp = None

        # Iterate over all the data points in the eeg data
        for channels, timestamp in eeg_data:
            # Update state
            while (next_marker_data is not None
                   and next_marker_data[1] < timestamp):
                # marker data is a tuple of the data and the timestamp
                # the data is a list of the marker types
                state = next_marker_data[0][0]

                next_marker_data = next(marker_data, None)

                if state == "starting":
                    print(f"Second 'Start' marker in the middle of file {filename}")

            if state == "stopped":
                break

            # Update gaze
            while next_gaze_data is not None and next_gaze_data[1] < timestamp:
                gaze_x, gaze_y = (
                    next_gaze_data[0][gaze_channel_i["x"]],
                    next_gaze_data[0][gaze_channel_i["y"]],
                )
                next_gaze_data = next(gaze_data, None)

                # Convert gaze x and y from pixels to mm
                gaze_x = px_to_mm_x(gaze_x)
                gaze_y = px_to_mm_y(gaze_y)

            # Update stimulus
            while (next_stimulus_data is not None
                   and next_stimulus_data[1] < timestamp):
                stimulus_x, stimulus_y = (
                    next_stimulus_data[0][stimulus_channel_i["x"]],
                    next_stimulus_data[0][stimulus_channel_i["y"]],
                )
                next_stimulus_data = next(stimulus_data, None)

                # Convert stimulus x and y from pixels to mm
                stimulus_x = px_to_mm_x(stimulus_x)
                stimulus_y = px_to_mm_y(stimulus_y)
            
            # Skip data points where the state, gaze or stimulus is None
            if None in [state, gaze_x, gaze_y, stimulus_x, stimulus_y]:
                continue

            first_timestamp = first_timestamp or timestamp

            # IMPORTANT: the order in which the elements are written to the csv
            # file must match the order defined in the header variable
            row = [
                timestamp - first_timestamp,
                channels[eeg_channel_i["TP9"]],
                channels[eeg_channel_i["AF7"]],
                channels[eeg_channel_i["AF8"]],
                channels[eeg_channel_i["TP10"]],
                # We don't include the "Right-Aux" channel
                gaze_x,
                gaze_y,
                stimulus_x,
                stimulus_y,
            ]
            writer.writerow(row)