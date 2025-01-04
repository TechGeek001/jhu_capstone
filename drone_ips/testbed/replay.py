"""This module contains the Replay class, which replays a recorded flight from a file instead of connecting to a flight controller."""

import time

import numpy as np
import pandas as pd
import zmq

import drone_ips.logging as ips_logging
import drone_ips.testbed as testbed
from drone_ips.monitor import ML_Ports


class Replay(testbed.Monitor):
    """This class replays a recorded flight from a file instead of connecting to a flight controller.

    Parameters
    ----------
    filename : str
        The name of the file containing the recorded flight data.
    **options : dict
        Additional options for the monitor.
    """

    # This code is embarassing, but we needed something quick. Make this better.

    def __init__(self, filename: str, **options: dict):
        # Load the raw data
        df = pd.read_csv(filename)
        df = df.replace({np.nan: None})
        df = df.drop(columns=["ml_verdict"])
        self._replay_data = df.to_dict(orient="records")
        self._realtime = options.get("realtime", False)
        self._current_i = 0

        self._data: list[dict] = []
        self._logger = ips_logging.LogManager.get_logger("monitor")
        self._csv_writer = ips_logging.CSVLogger()
        self.attack_manager = testbed.AttackManager()
        self.attack_manager._start_time = self._replay_data[0]["timestamp"]

        # Create socket objects to talk to the ML programs
        context = zmq.Context()
        #  Socket to talk to server
        self._sockets = {
            ML_Ports.GPS.value: context.socket(zmq.REQ),  # GPS
            ML_Ports.LIDAR.value: context.socket(zmq.REQ),  # LiDAR
            ML_Ports.COMPANION_COMPUTER.value: context.socket(zmq.REQ),  # Compaion Computer
        }
        for port, obj in self._sockets.items():
            obj.connect(f"tcp://localhost:{port}")
            obj.RCVTIMEO = self.MQZ_TIMEOUT

    def start(self):
        """Start the monitor and begin listening for messages."""
        self._start_time = int(time.time())
        self._start_new_logfile()
        self._event_loop()

    def _event_loop(self):
        """The main event loop for the monitor."""
        while self._current_i < len(self._replay_data):
            current_data = self.get_vehicle_data()
            # Log the data and append it to the list
            self._csv_writer.log(current_data)
            self._data.append(current_data)
            # If realtime is selected, wait for the next data point
            if self._realtime and self._current_i < len(self._replay_data):
                time.sleep(self._replay_data[self._current_i]["timestamp"] - current_data["timestamp"])

    def get_vehicle_data(self) -> dict:
        """Get the current data from the vehicle.

        Returns
        -------
        dict
            The current data from the vehicle.
        """
        current_data = self._replay_data[self._current_i]
        self._current_i += 1
        # This is where simulated attacks are injected
        current_data.update(self.attack_manager.attack(current_data, self.last_data))
        # Enrich the data with additional fields in place
        self._enrich_vehicle_data(current_data)
        return current_data

    def stop(self):
        """Stop the monitor and stop listening for messages."""
        pass
