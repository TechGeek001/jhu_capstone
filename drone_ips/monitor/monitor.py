"""Monitor module for the drone_ips package."""

import time
from typing import Any, Optional

import dronekit

import drone_ips.logging as ips_logging
import drone_ips.utils as ips_utils


class Monitor:
    """A class for monitoring the vehicle's data stream.

    Parameters
    ----------
    conn_str : str
        The connection string for the vehicle.
    **options : dict
        Additional options for the monitor.
    """

    POLL_INTERVAL: float = 0.5
    POLL_WHILE_DISARMED: bool = False

    def __init__(self, conn_str: str, **options: dict):
        self.conn_str = conn_str
        self.logger = ips_logging.LogManager.get_logger("monitor")
        self.vehicle: Optional[dronekit.Vehicle] = None
        self._data: list[dict] = []
        self.csv_writer = ips_logging.CSVLogger()
        # Set the options (silently ignore any unknown options)
        self.POLL_WHILE_DISARMED = options.get("always_poll", False)  # type: ignore
        self.POLL_INTERVAL = options.get("poll_interval", Monitor.POLL_INTERVAL)  # type: ignore

    @property
    def last_data(self) -> Optional[dict]:
        """Get the last data point from the monitor.

        Returns
        -------
        dict
            The last data point from the monitor, if it exists.
        """
        return self._data[-1] if len(self._data) > 0 else None

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
        current_data.update(self._enriched_vehicle_data(current_data))
        # Put the ML model here
        return current_data

    def start(self):
        """Start the monitor and begin listening for messages."""
        self._start_time = int(time.time())
        # Connect to the MAVLink stream using DroneKit
        self.logger.info(f"Listening for vehicle heartbeat on {self.conn_str}...")
        try:
            self.vehicle = dronekit.connect(self.conn_str, wait_ready=True)
            self._actions_vehicle_first_connected()
            self._event_loop()
        except dronekit.APIException:
            self.logger.error("Connection timed out")

    def stop(self):
        """Stop the monitor and close the vehicle connection."""
        if self.vehicle is not None:
            # Close the vehicle connection
            self.vehicle.close()
            self.logger.info("Connection closed.")

    def _actions_vehicle_first_connected(self):
        """Take action when the vehicle is first connected."""
        self.logger.info("Vehicle connected.")
        # If POLL_WHILE_DISARMED is True, create the log file;
        # otherwise it is created when the vehicle is first armed
        if self.POLL_WHILE_DISARMED:
            self._start_new_logfile()
        # TODO: make this a file and an arg for the CLI, perhaps
        corrected_values = {
            "COM_RAM_MAX": -1.0,
            "COM_CPU_MAX": -1.0,
            "COM_POWER_COUNT": 0,
        }
        # Ensure parameters are correct
        assert self.vehicle is not None  # for mypy
        for key, value in corrected_values.items():
            if self.vehicle.parameters[key] != value:
                # If the vehicle is not armed, update the parameter
                if not self.vehicle.armed:
                    self.logger.info(f"Setting parameter {key} ({self.vehicle.parameters[key]} => {value})")
                    self.vehicle.parameters[key] = value
                    # If the parameter didn't update, warn the user (this is because we can't catch the dronekit error directly)
                    if self.vehicle.parameters[key] != value:
                        self.logger.warning(f"Failed to update parameter {key}")
                # Else, only warn the user that the parameter doesn't match the expected value (for safety)
                else:
                    self.logger.warning(
                        f"Cannot update parameter {key} while armed ({self.vehicle.parameters[key]} != {value})"
                    )

    def _actions_if_vehicle_armed(self):
        """Take action when the event loop runs and the vehicle is armed."""
        # The vehicle will always be polled when armed
        self._poll_vehicle()

    def _actions_if_vehicle_disarmed(self):
        """Take action when the event loop runs and the vehicle is disarmed."""
        # Poll the vehicle for data if the correct flag is set
        if self.POLL_WHILE_DISARMED:
            self._poll_vehicle()

    def _event_loop(self):
        """The main event loop for the monitor."""
        if not isinstance(self.vehicle, dronekit.Vehicle):
            raise RuntimeError("Vehicle connection not established.")
        try:
            armed_state = False
            while True:
                # Determine the vehicle's arming state, and if it changed
                if self.vehicle.armed:
                    # If the vehicle was previously disarmed, trigger the state change actions
                    if not armed_state:
                        armed_state = True
                        self._on_state_change_armed()
                    self._actions_if_vehicle_armed()
                else:
                    # If the vehicle was previously armed, trigger the state change actions
                    if armed_state:
                        armed_state = False
                        self._on_state_change_disarmed()
                    self._actions_if_vehicle_disarmed()
                # Sleep for a short duration before polling the vehicle again
                time.sleep(self.POLL_INTERVAL)

        except KeyboardInterrupt:
            self.logger.info("Stopped listening for messages.")
            self.stop()

    def _enriched_vehicle_data(self, current_data: dict) -> dict:
        """Calculate enriched data fields from the vehicle data.

        Parameters
        ----------
        current_data : dict
            The current data from the vehicle.

        Returns
        -------
        dict
            The enriched vehicle data fields.
        """
        enriched_data: dict[str, Any] = {}
        # enriched_data: dict[str, Any] = {
        #     "delta": self.last_data["location.global_frame.lat"] - current_data["location.global_frame.lon"],
        # }
        return enriched_data

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

    def _on_state_change_armed(self):
        """Take action when the vehicle is first armed."""
        self.logger.info("Vehicle is now armed.")
        # If POLL_WHILE_DISARMED is False, create the log file now;
        # otherwise it was created when the vehicle was first connected
        if not self.POLL_WHILE_DISARMED:
            self._start_new_logfile()

    def _on_state_change_disarmed(self):
        """Take action when the vehicle is first disarmed."""
        self.logger.info("Vehicle is now disarmed.")
        # If POLL_WHILE_DISARMED is False, close the log file now;
        # otherwise it will be closed when the monitor stops
        if not self.POLL_WHILE_DISARMED:
            self.csv_writer.close()

    def _poll_vehicle(self):
        """Poll the vehicle for data."""
        # Get the vehicle's data and log it
        self.logger.debug("Requesting vehicle data...")
        current_data = self.get_vehicle_data()
        # Log the data and append it to the list
        self.csv_writer.log(current_data)
        self._data.append(current_data)

    def _start_new_logfile(self):
        """Start a new log file for the monitor."""
        self.csv_writer.open(f"logs/{ips_utils.format.datetime_str()}_data.csv")
