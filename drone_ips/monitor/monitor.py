"""Monitor module for the drone_ips package."""

import time
from typing import Any, Optional

import dronekit

import drone_ips.logging as ips_logging
import drone_ips.monitor as ips_monitor
import drone_ips.utils as ips_utils


class Monitor:
    """A class for monitoring the vehicle's data stream.

    Parameters
    ----------
    conn_str : str
        The connection string for the vehicle.
    """

    POLL_INTERVAL = 0.5

    def __init__(self, conn_str: str):
        self.conn_str = conn_str
        self.logger = ips_logging.LogManager.get_logger("monitor")
        self.vehicle: Optional[dronekit.Vehicle] = None
        self._data: list[dict] = []
        self._vehicle_armed_state = False
        self.csv_writer = ips_logging.CSVLogger()

    @property
    def last_data(self) -> Optional[dict]:
        """Get the last data point from the monitor.

        Returns
        -------
        dict
            The last data point from the monitor, if it exists.
        """
        return self._data[-1] if len(self._data) > 0 else None

    def start(self):
        """Start the monitor and begin listening for messages."""
        self._start_time = int(time.time())
        # Connect to the MAVLink stream using DroneKit
        self.logger.info(f"Connecting to vehicle on {self.conn_str}...")
        try:
            self.vehicle = dronekit.connect(self.conn_str, wait_ready=True)
            self._event_loop()
        except dronekit.APIException:
            self.logger.error("Connection timed out")

    def stop(self):
        """Stop the monitor and close the vehicle connection."""
        if self.vehicle is not None:
            # Close the vehicle connection
            self.vehicle.close()
            self.logger.info("Connection closed.")

    def _event_loop(self):
        """The main event loop for the monitor."""
        if not isinstance(self.vehicle, dronekit.Vehicle):
            raise RuntimeError("Vehicle connection not established.")
        try:
            self.logger.info("Connection successful. Waiting for vehicle to arm.")
            while True:
                # Only gather data if the vehicle is armed
                if self.vehicle.armed:
                    if not self._vehicle_armed_state:
                        self._vehicle_armed_state = True
                        self._actions_vehicle_first_armed()
                    self._actions_vehicle_armed()
                else:
                    if self._vehicle_armed_state:
                        self._vehicle_armed_state = False
                        self._actions_vehicle_first_disarmed()
                    self._actions_vehicle_disarmed()
                # Sleep for a short duration to keep the script alive
                time.sleep(Monitor.POLL_INTERVAL)

        except KeyboardInterrupt:
            self.logger.info("Stopped listening for messages.")
            self.stop()

    def _actions_vehicle_first_armed(self):
        """Take action when the vehicle is first armed."""
        # Create the new log file
        self.logger.info("Vehicle is now armed; logging data.")
        self.csv_writer.open(f"logs/{ips_utils.format.datetime_str()}_data.csv")

    def _actions_vehicle_armed(self):
        """Take action when the event loop runs and the vehicle is armed."""
        # Get the vehicle's data and log it
        self.logger.debug("Requesting vehicle data...")
        current_data = self.get_vehicle_data()
        # Hook the ML in here
        self.csv_writer.log(current_data)
        self._data.append(current_data)

    def _actions_vehicle_first_disarmed(self):
        """Take action when the vehicle is first disarmed."""
        # Close the CSV logger if the vehicle is not armed
        if self.csv_writer.file_open:
            self.logger.info("Vehicle is now disarmed; not logging data.")
            self.csv_writer.close()

    def _actions_vehicle_disarmed(self):
        """Take action when the event loop runs and the vehicle is disarmed."""
        self.logger.debug("Waiting for vehicle to arm...")

    def get_vehicle_data(self) -> dict:
        """Get the current data from the vehicle.

        Returns
        -------
        dict
            The current data from the vehicle.
        """
        current_data: dict[str, Any] = {
            "timestamp": time.time(),
        }
        current_data.update(ips_utils.misc.flatten_dict(self._get_vehicle_data_recursive(self.vehicle)))
        current_data.update(self._enrich_vehicle_data(current_data))
        return current_data

    def _enrich_vehicle_data(self, current_data: dict) -> dict:
        """Enrich the vehicle data with additional information.

        Parameters
        ----------
        current_data : dict
            The current data from the vehicle.

        Returns
        -------
        dict
            The enriched vehicle data.
        """
        return {}

    def _get_vehicle_data_recursive(self, obj: Any) -> dict:
        """Recursively get the properties in the vehicle object.

        Parameters
        ----------
        obj : Any
            The object to get the data from.

        Returns
        -------
        dict
            The data from the vehicle object.
        """
        # Initialize the working dictionary
        working_dict = {}
        # The dronekit.Vehicle object has attrs that cause problems
        if isinstance(obj, dronekit.Vehicle):
            pattern = r"(?!(_|capabilities|channels))\w+"
        # The dronekit.Channels object is a subclass of dict
        elif isinstance(obj, (dronekit.Channels, dronekit.ChannelsOverride)):
            # Add the channel values
            for k, v in obj.items():
                working_dict[k] = v
            # Don't add the "count" property
            pattern = r"(?!(_|count))\w+"
        else:
            pattern = r"(?!_)\w+"
        # Iterate through the object's properties and handle them
        for k, o in ips_utils.misc.get_object_properties(obj, pattern).items():
            # If the object belongs to the dronekit module, get its internal keys
            if hasattr(o, "__module__") and o.__module__ == "dronekit":
                working_dict[k] = self._get_vehicle_data_recursive(o)
            # Else, if this object is from the pymavlink module, ignore it
            elif hasattr(o, "__module__") and o.__module__ == "pymavlink.dialects.v20.ardupilotmega":
                continue
            # Else, if this belongs to some other module, report it and move on
            elif hasattr(o, "__module__") and o.__module__ != "builtins":
                self.logger.debug(f"Skipping object {k} from module {o.__module__}")
            # Else, simply add the value to the working dictionary
            else:
                working_dict[k] = o
        return working_dict
