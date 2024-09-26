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
If you are not creating a development environment, move to the next section.
```
pip install -r requirements_dev.txt
pre-commit install
pre-commit run
```

## Install Required Packages
```
pip install -r requirements.txt
```