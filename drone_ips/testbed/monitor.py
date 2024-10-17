"""This module extends the Monitor base class to facilitate testing."""

import drone_ips.monitor as ips_mon
import drone_ips.testbed as ips_tb


class Monitor(ips_mon.Monitor):
    """This class extends the Monitor base class to facilitate testing.

    Parameters
    ----------
    conn_str : str
        The connection string for the vehicle.
    """

    def __init__(self, conn_str: str):
        super().__init__(conn_str)
        # Add the attack manager to this version of the Monitor
        self.attack_manager = ips_tb.AttackManager()

    def get_vehicle_data(self) -> dict:
        """Get the current data from the vehicle.

        Returns
        -------
        dict
            The current data from the vehicle.
        """
        current_data = super().get_vehicle_data()
        # This is where simulated attacks are injected
        current_data.update(self.attack_manager.attack(current_data))
        return current_data

    def _actions_vehicle_first_armed(self):
        """Take action when the vehicle is first armed.

        This method extends the base Monitor class to additionally start the
        attack manager when the vehicle is armed to facilitate launching attacks.
        """
        super()._actions_vehicle_first_armed()
        # Additionally, reset the start_time for the attack manager
        self.attack_manager.start()
