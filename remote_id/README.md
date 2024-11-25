initialize submodules with:
```
git submodule update --init
cd transmitter-linux
git submodule update --init
```

initialize hostapd with: 
```
sudo apt install build-essential git libpcap-dev libsqlite3-dev binutils-dev bc pkg-config libssl-dev libiberty-dev libdbus-1-dev libnl-3-dev libnl-genl-3-dev libnl-route-3-dev
cd hostapd/hostapd
cp defconfig .config
make -j4
cd -
```

initialize gpsd with:
```
sudo apt install scons
cd gpsd
sed -i 's/\(variantdir *=\).*$/\1 "gpsd-dev"/' SConstruct
scons minimal=yes shared=True gpsd=False gpsdclients=False socket_export=yes
cd -
cd -
```

compile new_scheme with:
```
sudo apt install openssl cmake make
mkdir build && cd build
cmake ../.
make -j4
```

transmit with:
```
sudo ./new_scheme l
```