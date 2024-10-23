"""Application entry point."""

import argparse


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
    parser.add_argument("connection_string", type=str, help="the connection string for the vehicle.")
    parser.add_argument(
        "-a", "--always-poll", action="store_true", help="poll the vehicle and log data even when it is disarmed."
    )
    parser.add_argument("-t", "--testbed", action="store_true", help="run the monitor in testbed mode.")
    parser.add_argument(
        "-i", "--poll-interval", type=float, default=0.5, help="the interval at which to poll the vehicle."
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
    m.start()


def start_testbed_monitor(args: argparse.Namespace):
    """Start the testbed monitor with the given connection string.

    Parameters
    ----------
    args : argparse.Namespace
        The parsed command-line arguments.
    """
    from drone_ips.testbed import Monitor

    m = Monitor(args.connection_string, **vars(args))
    m.attack_manager.add_test("static_gps_spoofer", time_window=(5, 30))
    m.start()


if __name__ == "__main__":
    args = parse_args()
    start_func = start_monitor if not args.testbed else start_testbed_monitor
    start_func(args)
