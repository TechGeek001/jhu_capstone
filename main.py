from drone_ips.monitor import Monitor

if __name__ == "__main__":
    m = Monitor("udp:127.0.0.1:14540")
    m.start()
