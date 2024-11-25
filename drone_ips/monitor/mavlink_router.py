"""Convenience class to manage interconnections and the MAVLink router daemon."""

import ipaddress
import platform
import re
import subprocess
from typing import Optional

import drone_ips.logging as ips_logging


class MAVLinkManager:
    """Convenience class to manage interconnections and the MAVLink router daemon.

    This class is used to invoke MAVLink Router as a subprocess, which
    is easier than invoking it on the companion computer in a separate
    terminal window. This also makes it possible to include the output
    from MAVLink Router in the monitor's log file, because it is read in
    the event loop.

    Parameters
    ----------
    conn_str : str
        The connection string for the master vehicle.

    Examples
    --------
    Start mavlink-routerd with a connection string and pre-determined endpoints:
    """

    def __init__(self, conn_str: str):
        self._logger = ips_logging.LogManager.get_logger("mavlink_router")

        # This class is only designed to work on Linux
        if not MAVLinkManager.os_supported():
            raise RuntimeError("This class is only supported on Linux.")
        if not self.mavlink_routerd_available():
            raise RuntimeError("mavlink-routerd is not available on this system.")

        self._conn_str = conn_str  # The connection string for the vehicle
        self._process: Optional[subprocess.Popen] = (
            None  # Holds the subprocess, which is persistent until terminated manually
        )

    @property
    def conn_str(self) -> str:
        """The connection string for the master vehicle.

        Returns
        -------
        str
            The connection string for the master vehicle.
        """
        return self._conn_str

    @property
    def running(self) -> bool:
        """Check if the MAVLink router daemon is running.

        Returns
        -------
        bool
            True if the MAVLink router daemon is running, False otherwise.
        """
        return self._process is not None and self._process.poll() is None

    def get_connected_clients(self, ap_interface: str) -> tuple[str, ...]:
        """Get the IP addresses of clients connected to the specified access point interface.

        Parameters
        ----------
        ap_interface : str
            The name of the access point interface (e.g., "wlan0").

        Returns
        -------
        tuple of str
            A tuple of IP addresses of clients connected to the access point.
        """
        # Get the network for the interface
        network = self.get_ap_network(ap_interface)
        # Use `arp -a` to get the ARP table
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True)

        clients = []
        # Check each line for IP addresses within the same network
        for line in result.stdout.splitlines():
            ip_match = re.search(r"\((\d+\.\d+\.\d+\.\d+)\)", line)
            if ip_match:
                client_ip = ipaddress.IPv4Address(ip_match.group(1))
                if client_ip in network:
                    self._logger.info(f"Client connected with IP: {client_ip}")
                    clients.append(str(client_ip))
        return tuple(clients)

    def start(self, *endpoints: str):
        """Start the mavlink-routerd process with the specified connection and endpoints.

        Parameters
        ----------
        *endpoints : str
            The MAVLink endpoints to connect to the router daemon.
        """
        if self.running:
            self.stop()
        endpoint_args = [f"-e {endpoint}" for endpoint in endpoints]
        command = ["mavlink-routerd", *endpoint_args, self.conn_str]
        self._process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True  # Capture output as text
        )

    def poll(self) -> list[str]:
        """Poll available messages from the mavlink-routerd process output in a non-blocking manner.

        Returns
        -------
        list of str
            List of output messages from the MAVLink router.
        """
        if self._process is None or self._process.poll() is not None:
            raise RuntimeError("MAVLink router is not running.")

        messages = []
        # Read all available lines without blocking
        while True:
            output = self._process.stdout.readline()  # type: ignore
            if output:
                messages.append(output.strip())
                self._logger.info(f"MAVLink Router output: {output.strip()}")
            else:
                break  # Stop when no more output is immediately available
        return messages

    def stop(self):
        """Stop the mavlink-routerd process if it is running."""
        if self.running:
            self._logger.info("Stopping MAVLink Router daemon.")
            if self._process is not None:
                self._process.terminate()
                self._process.wait()

    @classmethod
    def mavlink_routerd_available(cls) -> bool:
        """Check if the MAVLink router daemon is available.

        Returns
        -------
        bool
            True if the MAVLink router daemon is available on this OS, False otherwise.
        """
        if cls.os_supported():
            return subprocess.run(["which", "mavlink-routerd"], capture_output=True, text=True).returncode == 0
        return False

    @staticmethod
    def os_supported() -> bool:
        """Check if the current OS is supported.

        Returns
        -------
        bool
            True if the current OS is supported, False otherwise.
        """
        return platform.system() == "Linux"

    @staticmethod
    def get_ap_network(interface: str) -> ipaddress.IPv4Network:
        """Retrieve the IP address of the specified network interface using `ip` command.

        Parameters
        ----------
        interface : str
            The name of the network interface (e.g., "wlan0").

        Returns
        -------
        ipaddress.IPv4Network
            The IP address assigned to the interface, or None if not found.
        """
        # Run `ip addr show <interface>` to get IP and subnet mask
        result = subprocess.run(["ip", "-o", "-f", "inet", "addr", "show", interface], capture_output=True, text=True)

        # Extract the IP and CIDR prefix
        match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/(\d+)", result.stdout)
        if match:
            ip_address = match.group(1)
            subnet_prefix = int(match.group(2))

            # Construct IPv4Network object
            network = ipaddress.IPv4Network(f"{ip_address}/{subnet_prefix}", strict=False)
            return network

        raise RuntimeError(f"No IP address found for interface {interface}.")
