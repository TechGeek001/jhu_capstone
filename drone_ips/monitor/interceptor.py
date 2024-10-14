"""This module contains the TestManager class, which is responsible for managing the tests that are run on the UUTs."""

from typing import Optional

import drone_ips.logging as logging
import drone_ips.utils as ips_utils


class TestBaseClass:
    """A base class for defining test scenarios for drone interception.

    Parameters
    ----------
    time_window : tuple[float, float], optional
        The time window during which the attack is active (None if always on).
    region : tuple[tuple[float, float], tuple[float, float]], optional
        The geographical region where the attack takes place (None if everywhere).
    """

    def __init__(
        self,
        time_window: Optional[tuple[Optional[float], Optional[float]]] = None,
        region: Optional[tuple[float, float, float, float]] = None,
    ):
        # Specify the time range when this attack is active
        self.time_window = time_window
        self.region = region

    def conditions_met(self, uut_data: dict) -> bool:
        """Check if the vehicle is inside the time window and geographical region for the attack.

        Parameters
        ----------
        uut_data : dict
            The data dictionary of the UUT.

        Returns
        -------
        bool
            True if the conditions are met, False otherwise.
        """
        clauses = [
            # Check if the current time is within the attack time window
            self.time_window is None,
            # Check if the UUT's location is within the attack region
            self.region is None
            or (
                self.region[0] <= uut_data["location.global_frame.lat"] <= self.region[2]
                and self.region[1] <= uut_data["location.global_frame.lon"] <= self.region[3]
            ),
        ]
        return all(clauses)

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

        Raises
        ------
        NotImplementedError
            If the attack method is not implemented in the subclass.

        Notes
        -----
        This method accepts the UUT data, but does not use it. It is present in the
        method's signature to maintain consistency with its child classes.
        """
        raise NotImplementedError


class GPSJammer(TestBaseClass):
    """A test class for simulating GPS jamming attacks on drones."""

    def attack(self, uut_data: dict) -> dict:
        """Modify the GPS data provided by the vehicle.

        Parameters
        ----------
        uut_data : dict
            The data dictionary of the UUT.

        Returns
        -------
        dict
            The keys that were added/modified from the UUT dictionary.

        Notes
        -----
        This method accepts the UUT data, but does not use it. It is present in the
        method's signature to maintain consistency with its parent and sibling classes.
        """
        return {
            "gps_0.fix_type": 0,
            "gps_0.satellites_visible": 0,
            "attack_type": "gps_jamming",
        }


class GPSSpoofer(TestBaseClass):
    """A test class for simulating GPS spoofing attacks on drones."""

    def attack(self, uut_data: dict) -> dict:
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
        orig_lat, orig_lon = uut_data["location.global_frame.lat"], uut_data["location.global_frame.lon"]
        noisy_lat, noisy_lon = ips_utils.math.add_gaussian_noise(orig_lat, orig_lon)
        return {
            "location.global_frame.lat": noisy_lat,
            "location.global_frame.lon": noisy_lon,
            "attack_type": "gps_spoofing",
        }


class TestManager:
    """A class for managing the tests that are run on the UUTs."""

    TEST_TYPES = {
        "gps_jammer": GPSJammer,
        "gps_spoofer": GPSSpoofer,
    }

    def __init__(self):
        self.logger = logging.LogManager.get_logger("manager")
        self._attack_battery: list[TestBaseClass] = []

    def add_test(self, test_type, *args, **kwargs):
        """Add a test to the attack battery.

        Parameters
        ----------
        test_type : str
            The type of test to add.
        *args : list
            The arguments to pass to the test constructor.
        **kwargs : dict
            The keyword arguments to pass to the test constructor.
        """
        self._attack_battery.append(TestManager.TEST_TYPES[test_type](*args, **kwargs))

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
        modified_data = {
            "attack_type": "benign",
        }
        for test in self._attack_battery:
            if test.conditions_met(uut_data):
                modified_data.update(test.attack(uut_data))
                # Assert that the attack type changed (development only)
                assert modified_data["attack_type"] != "benign"
                # Only allow one test to run at a time
                break
        return modified_data
