# Stimuli Presentation App & Control Plane

This repository contains the app used to present the stimili to the participants of the Consumer EEG-ET study. The app is divided into two programs, one run on the client side where the stimulus is shown, and one run on the server side (e.g. remotely) to control the state of the presentation.

## Setting up the Project

To set up the project, first create a python venv 
```
python -m venv .venv
```
Activate the venv and install the dependencies from the requirements.txt file
```
python -m pip install -r requirements.txt
```

## How to start the stimuli presentation app
```
python -m app.main
```

## How to start the control plane
```
python -m control_plane.main
```

## Important Notes

The Screen on which the stimuli are presented should be selected as primary display! Otherwise, the conversion from pixels to mm won't be correct. 