# Assured UAS Autonomy Capstone
TBD

## Development Environment Setup
If you are **not** creating a development environment, follow the directions for **Production Environment Setup** instead.

### Ubuntu 22.04 Virtual Machine (SITL Drone)
The SITL drone is installed on a virtual machine running Ubuntu 22.04. It is configured with 4 CPU cores and 8GB of RAM. These resources are necessary to run the flight controller simulator. The instructions below are from the [Ubuntu Development Environment](https://docs.px4.io/main/en/dev_setup/dev_env_linux_ubuntu.html) guide.
```
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
bash ./PX4-Autopilot/Tools/setup/ubuntu.sh
```
Downgrade gazebo with gazebo-classic, as instructed in the [Gazebo Classic Simulation](https://docs.px4.io/main/en/sim_gazebo_classic/) guide.
```
sudo apt remove gz-harmonic
sudo apt install aptitude
sudo aptitude install gazebo libgazebo11 libgazebo-dev
```
Download and install mavlink-router, which will enable communication to and from the SITL drone outside of localhost, according to the [mavlink-router](https://github.com/mavlink-router/mavlink-router) README file.
```
git clone https://github.com/mavlink-router/mavlink-router
cd mavlink-router
git submodule update --init --recursive
sudo apt install git meson ninja-build pkg-config gcc g++ systemd
meson setup build .
ninja -C build
sudo ninja -C build install
```

Because the VM does not have a GPU, the SITL simulator must be run in HEADLESS mode. Open two terminal windows or tabs.
#### SITL Terminal
```HEADLESS=1 SYS_FAILURE_EN=1 make px4_sitl gazebo-classic``` or ```HEADLESS=1 SYS_FAILURE_EN=1 make px4_sitl jmavsim```

#### Mavlink Router Terminal
```mavlink-routerd -e <development_machine_ip>:14550 -e <development_machine_ip>:14540 127.0.0.1:14550```  
- **UDP <development_machine_ip>:14550:** Is the port that QGroundControl (QGC) will communicate on
- **UDP <development_machine_ip>:14540:** Is the port that the Python IPS will communicate on
- **UDP 127.0.0.1:14550:** The internal port that mavlink-routerd is proxying
- **TCP 127.0.0.1:5760:** The internal port that the SITL drone communicates on - do not connect to this port

**Note:** It is possible to run this part of the environment in Windows Subsystem for Linux (WSL2), but I ran into issues (I suspect the Windows Defender Firewall) connecting the SITL drone to the custom Python script. This needs more testing; for now Linux works.

### Development Machine
The development machine is where the Python application will be developed. It facilitates communication over UDP to the SITL drone.

#### QGroundControl
Like Ardupilot's MissionPlanner, QGroundControl is used to send commands from the ground station to the drone. The PX4 community recommends QGroundControl over MissionPlanner, but both should work equally well Simply download and install [QGroundControl](https://qgroundcontrol.com/downloads/).

#### Python Virtual Environment
Because of dronekit's limitations, the latest version that works with this application is [Python 3.9.13](https://www.python.org/downloads/release/python-3913/); install it. Next, create your virtual environment. This is a good practice to prevent installing excessive modules in your global Python install.
```
python -m venv .venv
.venv\Scripts\activate
```
Finally, install the required development modules. They are meant to keep the code error-free and properly formatted.
```
pip install -r requirements.txt
pip install -r requirements_dev.txt
pre-commit install
pre-commit run
```

## Production Environment Setup
Because of dronekit's limitations, the latest version that works with this application is [Python 3.9.13](https://www.python.org/downloads/release/python-3913/); install it. Next, create your virtual environment. This is a good practice to prevent installing excessive modules in your global Python install.
```
python -m venv .venv
.venv\Scripts\activate
```
Finally, install the required development modules. They are meant to keep the code error-free and properly formatted.
```
pip install -r requirements.txt
```

## References
- Set Up PX4 Simulator on WSL [PX4 Simulator: Unlocking Drone Development and Testing Capabilities - Godfrey Nolan, RIIS LLC](https://www.youtube.com/watch?v=sRQQimoGxu8)