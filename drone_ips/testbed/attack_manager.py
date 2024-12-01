"""This module contains the TestManager class, which is responsible for managing the tests that are run on the UUTs."""

import random
import sys
import time
from typing import Optional

import drone_ips.logging as logging
import drone_ips.utils as ips_utils

# Static types
Region = tuple[tuple[float, float], tuple[float, float]]


class TestModule:
    """A base class for defining test scenarios for drone interception.

    Parameters
    ----------
    time_window : tuple[float, float], optional
        The time window during which the attack is active (None if always on).
    region : tuple[tuple[float, float], tuple[float, float]], optional
        The geographical region where the attack takes place (None if everywhere).

    Examples
    --------
    # A TestModule that is always active while the vehicle is armed
    >>> TestModule()

    # A TestModule that is inactive for the first 30 seconds after the vehicle is armed, then active until the end of the test
    >>> TestModule(time_window=(30, TestModule.WHEN_DISARMED))

    # A TestModule that is active for the first 30 seconds after the vehicle is armed, then inactive until the end of the test
    >>> TestModule(time_window=(TestModule.WHEN_ARMED, 30))

    # A TestModule that is active in a specific square region, bounded by GPS coordinates
    >>> TestModule(region=((39.245656, -76.385468), (39.235751, -76.354396)))

    # A TestModule that is active between 30-60 seconds after the vehicle is armed and flying in a specific region
    >>> TestModule(time_window=(30, 60), region=((39.245656, -76.385468), (39.235751, -76.354396)))
    """

    # Convenience constance for min/max time values
    WHEN_ARMED = -1
    WHEN_DISARMED = sys.maxsize
    LABEL = "test_runner"
    COUNT = 0

    def __init__(
        self,
        time_window: Optional[tuple[float, float]] = None,
        region: Optional[Region] = None,
    ):
        # Specify the time range when this attack is active
        self.logger = logging.LogManager.get_logger(f"attack_manager.{self.LABEL}:{TestModule.COUNT}")
        # Increment the counter
        TestModule.COUNT += 1
        self.time_window = time_window
        self.region = region

    def conditions_met(self, timedelta: float, uut_data: dict) -> bool:
        """Check if the vehicle is inside the time window and geographical region for the attack.

        Parameters
        ----------
        timedelta : float
            The time (in seconds) since the start of the test.
        uut_data : dict
            The data dictionary of the UUT.

        Returns
        -------
        bool
            True if all required conditions are met, False otherwise.
        """
        return all(
            [
                self._time_condition_met(timedelta),
                self._region_condition_met(uut_data),
            ]
        )

    def _time_condition_met(self, timedelta: float) -> bool:
        """Check if the current time delta is within the time window for the attack.

        Parameters
        ----------
        timedelta : float
            The time (in seconds) since the start of the test.

        Returns
        -------
        bool
            True if the time condition is met, False otherwise.
        """
        # If there is no time window, this attack is always on
        if self.time_window is None:
            return True
        # Else, check if the current time delta is within the window
        elif self.time_window[0] <= timedelta <= self.time_window[1]:
            return True
        return False

    def _region_condition_met(self, current_uut_data: dict) -> bool:
        """Check if the vehicle is within the geographical region for the attack.

        Parameters
        ----------
        current_uut_data : dict
            The current data dictionary of the UUT.

        Returns
        -------
        bool
            True if the region condition is met, False otherwise.
        """
        # If there is no region, this attack is always on
        if self.region is None:
            return True
        # Else, check if the UUT's location is within the region
        elif (
            self.region[0][0] <= current_uut_data["location.global_frame.lat"] <= self.region[1][0]
            and self.region[0][1] <= current_uut_data["location.global_frame.lon"] <= self.region[1][1]
        ):
            return True
        return False

    def attack(self, current_uut_data: dict, last_uut_data: Optional[dict]) -> dict:
        """Perform the attack on the UUT and return the modified data.

        Parameters
        ----------
        current_uut_data : dict
            The current data dictionary of the UUT.
        last_uut_data : dict, optional
            The previous data dictionary of the UUT.

        Returns
        -------
        dict
            The keys that were added/modified from the UUT dictionary.
        """
        # Ensure that the attack_type value is updated
        modified_values = {"attack_type": self.LABEL}
        # This method is meant to be extended by child classes
        modified_values.update(self.modify_values(current_uut_data, last_uut_data))
        self.log_changes(current_uut_data, modified_values)
        return modified_values

    def modify_values(self, current_uut_data: dict, last_uut_data: Optional[dict]) -> dict:
        """Add or modify specific values in the UUT data.

        This method is meant to be called after the attack method to modify the UUT data. Child
        classes should override this method to implement their own attack logic.

        Parameters
        ----------
        current_uut_data : dict
            The current data dictionary of the UUT.
        last_uut_data : dict, optional
            The previous data dictionary of the UUT.

        Returns
        -------
        dict
            The keys that were added/modified from the UUT dictionary.
        """
        return {}

    def log_changes(self, uut_data: dict, modified_dict: dict):
        """Log the changes made to the UUT data.

        Parameters
        ----------
        uut_data : dict
            The original data dictionary of the UUT.
        modified_dict : dict
            The modified data dictionary of the UUT.
        """
        changes = []
        for key, value in modified_dict.items():
            if key in uut_data:
                changes.append(f"{key}: {uut_data[key]} -> {value}")
            else:
                changes.append(f"{key}: {value}")
        if len(changes) > 0:
            log_string = "Modified the following value(s): " + ", ".join(changes)
        else:
            log_string = "No changes were made to the UUT data."
        self.logger.debug(log_string)


class GPSJammer(TestModule):
    """A test class for simulating GPS jamming attacks on drones."""

    LABEL = "gps_jammer"

    def modify_values(self, current_uut_data: dict, last_uut_data: Optional[dict]) -> dict:
        """Modify the GPS data provided by the vehicle.

        Parameters
        ----------
        current_uut_data : dict
            The current data dictionary of the UUT.
        last_uut_data : dict, optional
            The previous data dictionary of the UUT.

        Returns
        -------
        dict
            The keys that were added/modified from the UUT dictionary.
        """
        return {
            "gps_0.fix_type": 0,
            "gps_0.satellites_visible": 0,
        }


class StaticGPSSpoofer(TestModule):
    """A test class for simulating GPS static spoofing attacks on drones."""

    LABEL = "static_gps_spoofer"
    WHITE_HOUSE = (38.897957, -77.036560)
    MOSCOW = (55.755825, 37.617298)
    LONDON = (51.507351, -0.127758)

    def modify_values(self, current_uut_data: dict, last_uut_data: Optional[dict]) -> dict:
        """Modify the GPS data provided by the vehicle.

        This performs the attack by changing the location to a static location, typically marked as a no-fly zone.
        This is a common method of spoofing as the attacker does not need to know anything about where the drone is.

        Parameters
        ----------
        current_uut_data : dict
            The current data dictionary of the UUT.
        last_uut_data : dict, optional
            The previous data dictionary of the UUT.

        Returns
        -------
        dict
            The keys that were added/modified from current the UUT dictionary.
        """

        spoofed_lat, spoofed_lon = ips_utils.math.add_gaussian_noise(*self.WHITE_HOUSE)

        return {
            "location.global_frame.lat": spoofed_lat,
            "location.global_frame.lon": spoofed_lon,
        }


class SmartGPSSpoofer(TestModule):
    """A test class for simulating GPS active spoofing attacks on drones."""

    LABEL = "smart_gps_spoofer"

    def modify_values(self, current_uut_data: dict, last_uut_data: Optional[dict]) -> dict:
        """Modify the GPS data provided by the vehicle.

        This performs the attack with the goal of altering the intended direction of the drone.
        Requires an adversary with detection capabilities to track and spoof the location of the drone.

        Parameters
        ----------
        current_uut_data : dict
            The current data dictionary of the UUT.
        last_uut_data : dict, optional
            The previous data dictionary of the UUT.

        Returns
        -------
        dict
            The keys that were added/modified from the current UUT dictionary.
        """

        # If there is previous UUT data to work with, spoof the location based on the direction of the drone
        if last_uut_data is not None:
            # Directions: [0] North, [1] East, [2] South, [3] West
            direction = 0
            approx_delta = 0.0004

            spoofed_lat = (
                last_uut_data["location.global_frame.lat"] + -approx_delta * (direction - 1)
                if (direction % 2 == 0)
                else 0
            )
            spoofed_lon = (
                last_uut_data["location.global_frame.lon"] + -approx_delta * (direction - 2)
                if (direction % 2 == 1)
                else 0
            )
        # Else, leave the location unchanged for this iteration
        else:
            spoofed_lat = current_uut_data["location.global_frame.lat"]
            spoofed_lon = current_uut_data["location.global_frame.lat"]

        return {
            "location.global_frame.lat": spoofed_lat,
            "location.global_frame.lon": spoofed_lon,
        }


class LiDARSpoofer(TestModule):
    """A test class for simulating attacks on a drone's 1D LiDAR."""

    LABEL = "lidar_spoofer"

    def modify_values(self, current_uut_data: dict, last_uut_data: Optional[dict]) -> dict:
        """Modify the GPS data provided by the vehicle.

        Parameters
        ----------
        current_uut_data : dict
            The current data dictionary of the UUT.
        last_uut_data : dict, optional
            The previous data dictionary of the UUT.

        Returns
        -------
        dict
            The keys that were added/modified from the UUT dictionary.
        """
        return {
            "rangefinder.distance": random.randint(0, current_uut_data["rangefinder.distance"]),
        }


class AttackManager:
    """A class for managing the tests that are run on the UUTs."""

    TEST_TYPES = {
        "gps_jammer": GPSJammer,
        "static_gps_spoofer": StaticGPSSpoofer,
        "smart_gps_spoofer": SmartGPSSpoofer,
        "lidar_spoofer": LiDARSpoofer,
    }

    def __init__(self):
        self.logger = logging.LogManager.get_logger("attack_manager")
        self._attack_battery: list[TestModule] = []
        self._enabled = False
        self.start()

    def start(self):
        """Set the start time for the attack manager."""
        self._start_time = time.time()
        self._enabled = True

    def stop(self):
        """Stop the attack manager."""
        self._enabled = False

    def add_test(
        self, test_type: str, time_window: Optional[tuple[float, float]] = None, region: Optional[Region] = None
    ):
        """Add a test to the attack battery.

        Parameters
        ----------
        test_type : str
            The type of test to add.
        time_window : tuple[float, float], optional
            The time window during which the attack is active (None if always on).
        region : tuple[tuple[float, float], tuple[float, float]], optional
            The geographical region where the attack takes place (None if everywhere).
        """
        self._attack_battery.append(AttackManager.TEST_TYPES[test_type](time_window, region))

    def attack(self, current_uut_data: dict, last_uut_data: Optional[dict]) -> dict:
        """Simulate an attack on the vehicle by modifying the data it produces.

        Parameters
        ----------
        current_uut_data : dict
            The current data dictionary of the UUT.
        last_uut_data : dict, optional
            The previous data dictionary of the UUT.

        Returns
        -------
        dict
            The keys that were added/modified from the UUT dictionary.
        """
        if not self._enabled:
            self.logger.warning("attack() method called while the AttackManager is stopped.")
            return {}

        timedelta = current_uut_data["timestamp"] - self._start_time
        modified_data = {
            "attack_type": "benign",
        }
        for test in self._attack_battery:
            if test.conditions_met(timedelta, current_uut_data):
                self.logger.info(f"Conditions met for '{test.LABEL}' attack (timedelta = {round(timedelta, 2)}).")
                modified_data.update(test.attack(current_uut_data, last_uut_data))
                # Assert that the attack type changed (development only)
                assert modified_data["attack_type"] != "benign"
                # Only allow one test to run at a time
                break
        else:
            self.logger.debug(f"No attacks are currently active (timedelta = {round(timedelta, 2)}s).")
        return modified_data
