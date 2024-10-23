#!/bin/bash

# Define variables
CONFIG_FILE="/boot/firmware/config.txt"
UART_STRING="enable_uart=1"
BT_DISABLE_STRING="dtoverlay=disable-bt"
DIR_NAME="uas"
VENV_DIR="venv_test_mavproxy"
MASTER_PORT="/dev/ttyAMA0"

# Disable Bluetooth by editing config.txt
echo "Checking if Bluetooth is already disabled..."
if grep -q "$BT_DISABLE_STRING" "$CONFIG_FILE"; then
  echo "Bluetooth is already disabled in $CONFIG_FILE."
else
  echo "Disabling Bluetooth in $CONFIG_FILE..."
  # Check for 'enable_uart=1' and add it if missing
  if ! grep -q "$UART_STRING" "$CONFIG_FILE"; then
    echo "Enabling UART..."
    echo -e "\n[all]\n$UART_STRING" >> "$CONFIG_FILE"
  else
    echo "UART is already enabled."
  fi

  # Append the 'dtoverlay=disable-bt' under [all]
  echo "$BT_DISABLE_STRING" >> "$CONFIG_FILE"
  echo "Bluetooth disabled successfully."
fi

# Create the directory only if it doesn't exist
if [ ! -d "$DIR_NAME" ]; then
  echo "Creating directory $DIR_NAME..."
  mkdir "$DIR_NAME"
else
  echo "Directory $DIR_NAME already exists."
fi

# Navigate into the directory
cd "$DIR_NAME"

# Remove modemmanager if it's installed
echo "Checking for ModemManager..."
if dpkg-query -W -f='${Status}' modemmanager 2>/dev/null | grep -q "install ok installed"; then
  echo "Purging ModemManager..."
  sudo apt purge modemmanager -y
else
  echo "ModemManager is not installed."
fi

# Check if the virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating Python virtual environment..."
  python -m venv "$VENV_DIR"
else
  echo "Virtual environment $VENV_DIR already exists."
fi

# Activate the virtual environment
echo "Activating the virtual environment..."
source "$VENV_DIR/bin/activate"

# Check if mavproxy.py command is available and run it
if command -v mavproxy.py &>/dev/null; then
  echo "Running MAVProxy with master port $MASTER_PORT..."
  mavproxy.py --master="$MASTER_PORT"
else
  echo "MAVProxy is not installed. Please install it and try again."
fi
