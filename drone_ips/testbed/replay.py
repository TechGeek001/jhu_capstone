"""This module contains the Replay class, which replays a recorded flight from a file instead of connecting to a flight controller."""

import time

import numpy as np
import pandas as pd

import drone_ips.logging as ips_logging
import drone_ips.testbed as testbed


class Replay(testbed.Monitor):
    """This class replays a recorded flight from a file instead of connecting to a flight controller.

    Parameters
    ----------
    filename : str
        The name of the file containing the recorded flight data.
    """

    # This code is embarassing, but we needed something quick. Make this better.

    def __init__(self, filename: str):
        # Load the raw data
        df = pd.read_csv(filename)
        df = df.replace({np.nan: None})
        self._replay_data = df.to_dict(orient="records")
        self._current_i = 0

        self._data: list[dict] = []
        self._logger = ips_logging.LogManager.get_logger("monitor")
        self._csv_writer = ips_logging.CSVLogger()
        self.attack_manager = testbed.AttackManager()
        self.attack_manager._start_time = self._replay_data[0]["timestamp"]

    def start(self):
        """Start the monitor and begin listening for messages."""
        self._start_time = int(time.time())
        self._start_new_logfile()
        self._event_loop()

    def _event_loop(self):
        """The main event loop for the monitor."""
        while self._current_i < len(self._replay_data):
            current_data = self.get_vehicle_data()
            current_data.update(self._enriched_vehicle_data(current_data))
            # Put the ML model here
            # Add another entry in the dictionary with ML verdict
            current_data.update({"ml_verdict": "value_here"})
            # Log the data and append it to the list
            self._csv_writer.log(current_data)
            self._data.append(current_data)

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
        return current_data

    def stop(self):
        """Stop the monitor and stop listening for messages."""
        pass
