"""This module contains the TestManager class, which is responsible for managing the tests that are run on the UUTs."""

import sys
import time
from typing import Optional

import drone_ips.logging as logging
import drone_ips.utils as ips_utils


class TestRunner:
    """A base class for defining test scenarios for drone interception.

    Parameters
    ----------
    time_window : tuple[float, float], optional
        The time window during which the attack is active (None if always on).
    region : tuple[tuple[float, float], tuple[float, float]], optional
        The geographical region where the attack takes place (None if everywhere).

    Examples
    --------
    # A TestRunner that is always active while the vehicle is armed
    >>> TestRunner()

    # A TestRunner that is inactive for the first 30 seconds after the vehicle is armed, then active until the end of the test
    >>> TestRunner(time_window=(30, TestRunner.WHEN_DISARMED))

    # A TestRunner that is active for the first 30 seconds after the vehicle is armed, then inactive until the end of the test
    >>> TestRunner(time_window=(TestRunner.WHEN_ARMED, 30))

    # A TestRunner that is active in a specific square region, bounded by GPS coordinates
    >>> TestRunner(region=((39.245656, -76.385468), (39.235751, -76.354396)))

    # A TestRunner that is active between 30-60 seconds after the vehicle is armed and flying in a specific region
    >>> TestRunner(time_window=(30, 60), region=((39.245656, -76.385468), (39.235751, -76.354396)))
    """

    # Convenience constance for min/max time values
    WHEN_ARMED = -1
    WHEN_DISARMED = sys.maxsize
    LABEL = "test_runner"
    COUNT = 0

    def __init__(
        self,
        time_window: Optional[tuple[float, float]] = None,
        region: Optional[tuple[tuple[float, float], tuple[float, float]]] = None,
    ):
        # Specify the time range when this attack is active
        self.logger = logging.LogManager.get_logger(f"attack_manager.{self.LABEL}:{TestRunner.COUNT}")
        # Increment the counter
        TestRunner.COUNT += 1
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

    def _region_condition_met(self, uut_data: dict) -> bool:
        """Check if the vehicle is within the geographical region for the attack.

        Parameters
        ----------
        uut_data : dict
            The data dictionary of the vehicle under test.

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
            self.region[0][0] <= uut_data["location.global_frame.lat"] <= self.region[1][0]
            and self.region[0][1] <= uut_data["location.global_frame.lon"] <= self.region[1][1]
        ):
            return True
        return False

    def attack(self, uut_data: dict) -> dict:
        """Perform the attack on the UUT and return the modified data.

        Parameters
        ----------
        uut_data : dict
            The data dictionary of the UUT.

        Returns
        -------
        dict
            The keys that were added/modified from the UUT dictionary.
        """
        # Ensure that the attack_type value is updated
        modified_values = {"attack_type": self.LABEL}
        # This method is meant to be extended by child classes
        modified_values.update(self.modify_values(uut_data))
        self.log_changes(uut_data, modified_values)
        return modified_values

    def modify_values(self, uut_data: dict) -> dict:
        """Add or modify specific values in the UUT data.

        This method is meant to be called after the attack method to modify the UUT data. Child
        classes should override this method to implement their own attack logic.

        Parameters
        ----------
        uut_data : dict
            The data dictionary of the UUT.

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


class GPSJammer(TestRunner):
    """A test class for simulating GPS jamming attacks on drones."""

    LABEL = "gps_jammer"

    def modify_values(self, uut_data: dict) -> dict:
        """Modify the GPS data provided by the vehicle.

        Parameters
        ----------
        uut_data : dict
            The data dictionary of the UUT.

        Returns
        -------
        dict
            The keys that were added/modified from the UUT dictionary.
        """
        return {
            "gps_0.fix_type": 0,
            "gps_0.satellites_visible": 0,
        }


class StaticGPSSpoofer(TestRunner):
    """A test class for simulating GPS static spoofing attacks on drones."""

    LABEL = "static_gps_spoofer"

    def modify_values(self, uut_data: dict) -> dict:
        """Modify the GPS data provided by the vehicle. 
        This performs the attack by changing the location to a static location, typically marked as a no-fly zone.
        This is a common method of spoofing as the attacker does not need to know anything about where the drone is.

        Parameters
        ----------
        uut_data : dict
            The data dictionary of the UUT.

        Returns
        -------
        dict
            The keys that were added/modified from current the UUT dictionary.
        """

        """Some other fun locations to test spoofing
            The White House: (38.897957, -77.036560)
            Moscow: (55.755825, 37.617298)
            London: (51.507351, -0.127758)
        """
 
        spoofed_lat, spoofed_lon = ips_utils.math.add_gaussian_noise(38.897957, -77.036560)

        return {
            "location.global_frame.lat": spoofed_lat,
            "location.global_frame.lon": spoofed_lon,
        }

class SmartGPSSpoofer(TestRunner):
    """A test class for simulating GPS active spoofing attacks on drones."""

    LABEL = "smart_gps_spoofer"

    def modify_values(self, uut_data: dict, prev_uut_data: dict) -> dict:
        """Modify the GPS data provided by the vehicle.
        This performs the attack with the goal of altering the intended direction of the drone.
        Requires an adversary with detection capabilities to track and spoof the location of the drone.

        Parameters
        ----------
        uut_data : dict
            The data dictionary of the UUT.
        prev_uut_data : dict
            The dictionary of the previous (altered) UUT.

        Returns
        -------
        dict
            The keys that were added/modified from the current UUT dictionary.
        """


        """direction:
            0: North
            1: East
            2: South
            3: West
        """
        direction = 0

        approx_delta = 0.0004

        spoofed_lat = prev_uut_data["location.global_frame.lat"] + -approx_delta * (direction-1) if (direction % 2 == 0) else 0
        spoofed_lon = prev_uut_data["location.global_frame.lon"] + -approx_delta * (direction-2) if (direction % 2 == 1) else 0

        # noisy_lat, noisy_lon = ips_utils.math.add_gaussian_noise(
        #     uut_data["location.global_frame.lat"], uut_data["location.global_frame.lon"]
        # )

        return {
            "location.global_frame.lat": spoofed_lat,
            "location.global_frame.lon": spoofed_lon,
        }


class AttackManager:
    """A class for managing the tests that are run on the UUTs."""

    TEST_TYPES = {
        "gps_jammer": GPSJammer,
        "static_gps_spoofer": StaticGPSSpoofer,
        "smart_gps_spoofer": SmartGPSSpoofer,
    }

    def __init__(self):
        self.logger = logging.LogManager.get_logger("attack_manager")
        self._attack_battery: list[TestRunner] = []
        self.start()

    def start(self):
        """Set the start time for the attack manager."""
        self._start_time = time.time()

    def add_test(
        self,
        test_type: str,
        time_window: Optional[tuple[float, float]] = None,
        region: Optional[tuple[tuple[float, float], tuple[float, float]]] = None,
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

    def attack(self, uut_data: dict) -> dict:
        """Simulate an attack on the vehicle by modifying the data it produces.

        Parameters
        ----------
        uut_data : dict
            The data dictionary of the UUT.

        Returns
        -------
        dict
            The keys that were added/modified from the UUT dictionary.
        """
        timedelta = uut_data["timestamp"] - self._start_time
        modified_data = {
            "attack_type": "benign",
        }
        for test in self._attack_battery:
            if test.conditions_met(timedelta, uut_data):
                self.logger.info(f"Conditions met for '{test.LABEL}' attack (timedelta = {round(timedelta, 2)}).")
                modified_data.update(test.attack(uut_data))
                # Assert that the attack type changed (development only)
                assert modified_data["attack_type"] != "benign"
                # Only allow one test to run at a time
                break
        else:
            self.logger.debug(f"No attacks are currently active (timedelta = {round(timedelta, 2)}s).")
        return modified_data
