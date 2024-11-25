"""This module extends the Monitor base class to facilitate testing."""

import drone_ips.monitor as monitor
import drone_ips.testbed as testbed


class Monitor(monitor.Monitor):
    """This class extends the Monitor base class to facilitate testing.

    Parameters
    ----------
    conn_str : str
        The connection string for the vehicle.
    **options : dict
        Additional options for the monitor.
    """

    def __init__(self, conn_str: str, **options: dict):
        super().__init__(conn_str, **options)
        # Add the attack manager to this version of the Monitor
        self.attack_manager = testbed.AttackManager()

    def get_vehicle_data(self) -> dict:
        """Get the current data from the vehicle.

        Returns
        -------
        dict
            The current data from the vehicle.
        """
        current_data = super().get_vehicle_data()
        # This is where simulated attacks are injected
        current_data.update(self.attack_manager.attack(current_data, self.last_data))
        return current_data

    def _on_state_change_armed(self):
        """Take action when the vehicle is first armed.

        This method extends the base Monitor class to additionally start the
        attack manager when the vehicle is armed to facilitate launching attacks.
        """
        super()._on_state_change_armed()
        # Additionally, reset the start_time for the attack manager
        self.attack_manager.start()

    def _on_state_change_disarmed(self):
        """Take action when the vehicle is first disarmed."""
        super()._on_state_change_disarmed()
        # Additionally, stop the attack manager
        self.attack_manager.stop()
