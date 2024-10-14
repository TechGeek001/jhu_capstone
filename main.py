"""Application entry point."""

from drone_ips.monitor import Monitor, TestManager

if __name__ == "__main__":
    test_manager = TestManager()
    test_manager.add_test("gps_jammer")
    m = Monitor("udp:0.0.0.0:14540")
    m._interceptor = test_manager
    m.start()
