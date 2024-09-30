# Assured UAS Autonomy Capstone
TBD
## Install Python
Because of dronekit's limitations, the latest version that works with this application is [Python 3.9.13](https://www.python.org/downloads/release/python-3913/).
## Create Virtual Environment (Optional, Recommended)
Create Virtual Environment
```
python -m venv .venv
.venv\Scripts\activate
```
## Development Environment Setup
If you are **not** creating a development environment, move to the next section.
### Set up Python
```
pip install -r requirements_dev.txt
pre-commit install
pre-commit run
```
### Set up SITL

#### Windows
The SITL simulation is run on Windows Subsystem for Linux (WSL).
- Install the latest version of WSL (_must_ be WSL2)
- 

#### Linux
If installing on a VM, you will likely not be able to have a GUI output.


### Set up QGroundControl
Like Ardupilot's MissionPlanner, QGroundControl is used to send commands from the ground station to the drone. The PX4 community recommends QGroundControl over MissionPlanner, but both should work equally well.
- Download and Install [QGroundControl](https://qgroundcontrol.com/downloads/)

## Install Required Packages
```
pip install -r requirements.txt
```

## References
- Set Up PX4 Simulator on WSL [PX4 Simulator: Unlocking Drone Development and Testing Capabilities - Godfrey Nolan, RIIS LLC](https://www.youtube.com/watch?v=sRQQimoGxu8)