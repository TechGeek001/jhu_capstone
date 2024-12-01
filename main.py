"""Application entry point."""

import argparse
from typing import Union

import drone_ips


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns
    -------
    argparse.Namespace
        The parsed command-line arguments.
    """

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter, description="Monitor a drone's data stream."
    )
    parser.add_argument(
        "-c",
        "--connection_string",
        type=str,
        default="udp:0.0.0.0:14540",
        help="the connection string for the vehicle (default = 'udp:0.0.0.0:14540').",
    )
    parser.add_argument(
        "-a", "--always-poll", action="store_true", help="poll the vehicle and log data even when it is disarmed."
    )
    parser.add_argument("-t", "--testbed", action="store_true", help="run the monitor in testbed mode.")
    parser.add_argument("-r", "--replay", type=str, help="run the monitor in replay mode.")
    parser.add_argument(
        "-i", "--poll-interval", type=float, default=0.1, help="the interval at which to poll the vehicle."
    )
    return parser.parse_args()


def start_monitor(args: argparse.Namespace):
    """Start the monitor with the given connection string.

    Parameters
    ----------
    args : argparse.Namespace
        The parsed command-line arguments.
    """
    from drone_ips.monitor import Monitor

    m = Monitor(args.connection_string, **vars(args))
    # Start the monitor
    m.start()


def start_testbed_monitor(args: argparse.Namespace):
    """Start the testbed monitor with the given connection string.

    Parameters
    ----------
    args : argparse.Namespace
        The parsed command-line arguments.
    """
    from drone_ips.testbed import Monitor, Replay

    m: Union[Replay, Monitor]
    if args.replay:
        m = Replay(args.replay)
    else:
        m = Monitor(args.connection_string, **vars(args))
    # Define the test battery
    # m.attack_manager.add_test("static_gps_spoofer", time_window=(5, 30))
    m.attack_manager.add_test("lidar_spoofer", time_window=(5, 30))
    # Start the monitor with integrated Attack Manager
    m.start()


if __name__ == "__main__":
    print(f"UAV Monitor {drone_ips.__version__}")
    args = parse_args()
    start_func = start_monitor if not args.testbed else start_testbed_monitor
    start_func(args)
