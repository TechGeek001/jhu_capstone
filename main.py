from drone_ips.monitor import Monitor

if __name__ == "__main__":
    m = Monitor("udp:0.0.0.0:14540")
    m.start()
