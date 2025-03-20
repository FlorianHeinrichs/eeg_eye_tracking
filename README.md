# Consumer-Grade EEG Eye-Tracking Dataset

## Overview
This repository contains code related to the analysis/processing of a dataset, 
containing simultaneously recorded EEG and eye-tracking data with consumer-grade 
hardware.

## Dataset

The dataset used in this project is available on [Zenodo](https://zenodo.org/records/14860668) 
and can be accessed using the following DOI: [DOI link](https://doi.org/10.5281/zenodo.14860668).

> **Note**: A detailed data descriptor will be published in the future to 
> provide comprehensive information about the dataset, its variables, and how it 
> can be used.

## Project Structure

```
.
├── stimuli-presentation-app/ # Contains the app used to record the data
│   └── ...
├── analyse_data.py           # Calculate cross-correlation function between gaze and stimulus
├── impute_missing_values.py  # Impute missing values in raw recordings (measured as '0')
├── LICENSE                   # License for the repository
├── load_data.py              # Load (preprocessed) data and apply frequency filters
├── README.md                 # Project overview and documentation
├── utils.py                  # Utility functions for data handling (automatic download from Zenodo)
└── xdf_to_csv.py             # Convert raw XDF to CSV files
```

## Requirements

The required Python libraries to run the code, depend on the specific use case.
While most scripts mainly depend on `matplotlib`, `numpy`, `pandas`, `scipy` and 
`statsmodels`, the recording app is implemented with `PyQT6`.

## License

This project is licensed under the [MIT License](https://github.com/FlorianHeinrichs/eeg_eye_tracking?tab=MIT-1-ov-file#).

## Citation

If you use this code in your own work, please cite the following preprint:

- Vasconcelos Afonso, T. and Heinrichs, F. (2025). Consumer-grade eeg-based eye tracking. *arXiv preprint arXiv:2503.14322*.

BibTeX:

    @article{afonso2025,
    	title={Consumer-grade EEG-based Eye Tracking},
    	author={Vasconcelos Afonso, Tiago and Heinrichs, Florian},
    	journal={arXiv preprint arXiv:2503.14322},
    	year={2025}
    }
