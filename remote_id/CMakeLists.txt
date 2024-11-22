# Copyright (C) 2021, Soren Friis
#
# SPDX-License-Identifier: Apache-2.0
#
# Open Drone ID Linux transmitter example.
#
# Maintainer: Soren Friis
# friissoren2@gmail.com

cmake_minimum_required (VERSION 3.10)

project (opendroneid-new_scheme)

SET(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DCONFIG_CTRL_IFACE -DCONFIG_CTRL_IFACE_UNIX")

if(DEFINED ODID_AUTH_MAX_PAGES)
    message(STATUS "Using externally defined ODID_AUTH_MAX_PAGES value")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DODID_AUTH_MAX_PAGES=${ODID_AUTH_MAX_PAGES}")
endif()

if(DEFINED ODID_BASIC_ID_MAX_MESSAGES)
    message(STATUS "Using externally defined ODID_BASIC_ID_MAX_MESSAGES value")
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DODID_BASIC_ID_MAX_MESSAGES=${ODID_BASIC_ID_MAX_MESSAGES}")
endif()

include_directories(
        transmitter-linux/hostapd/src
        transmitter-linux/hostapd/src/utils
        transmitter-linux/core-c/libopendroneid
        transmitter-linux/gpsd/gpsd-dev
        transmitter-linux/bluez
)

add_executable(new_scheme
        transmitter-linux/hostapd/src/utils/os_unix.c
        transmitter-linux/hostapd/src/common/cli.c
        transmitter-linux/hostapd/src/common/wpa_ctrl.c
        transmitter-linux/hostapd/src/utils/common.c
        transmitter-linux/hostapd/src/utils/edit.c
        transmitter-linux/hostapd/src/utils/eloop.c
        transmitter-linux/hostapd/src/utils/wpa_debug.c
        transmitter-linux/core-c/libopendroneid/opendroneid.c
        transmitter-linux/bluez/lib/hci.c
        transmitter-linux/bluez/lib/bluetooth.c
        transmitter-linux/ap_interface.c
        transmitter-linux/utils.c
        transmitter-linux/bluetooth.c
        transmitter-linux/wifi_beacon.c
        transmitter-linux/gpsmod.c
        new_scheme.c
        transmitter-linux/print_bt_features.c
)

target_link_libraries(new_scheme
        pthread
        m
        "${PROJECT_SOURCE_DIR}/transmitter-linux/gpsd/gpsd-dev/libgps.so"
)
