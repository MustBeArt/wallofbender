#!./capython3
# To avoid running as root, we use a copy of the Python3 interpreter.
# Give it the needed capabilities with this command:
# sudo setcap 'cap_net_raw,cap_net_admin+eip' capython3

# Portions of the Bluetooth interaction parts of this script have been
# taken from https://stackoverflow.com/questions/23788176/finding-bluetooth-low-energy-with-python


import sys
import os
import struct
import signal
import time
from ctypes import (CDLL, get_errno)
from ctypes.util import find_library
from socket import (
    socket,
    AF_BLUETOOTH,
    SOCK_RAW,
    BTPROTO_HCI,
    SOL_HCI,
    HCI_FILTER,
)

BADGE_YEAR_NOW = "yr"     # year (Appearance field) in most recent advertisement
BADGE_YEARS = "yrs"       # list of years seen for this address
BADGE_NAME_NOW = "nm"     # badge name (Complete Local Name) in most recent
BADGE_NAMES = "nms"       # list of names seen for this address
BADGE_ID_NOW = "id"       # badge ID (first two octets of Manufacturer Specific Data)
BADGE_IDS = "ids"         # list of badge IDs seen for this address
BADGE_TIME = "tm"         # time of most recent advertisement received
BADGE_ADDR = "ad"         # Advertising Address for this badge (assumed constant)
BADGE_CNT = "n"           # number of advertisements received from this address

badges = {}

btlib = find_library("bluetooth")
if not btlib:
    raise Exception(
        "Can't find required bluetooth libraries"
        " (need to install bluez)"
    )
bluez = CDLL(btlib, use_errno=True)

dev_id = bluez.hci_get_route(None)

sock = socket(AF_BLUETOOTH, SOCK_RAW, BTPROTO_HCI)
if not sock:
    print("Failed to open Bluetooth")
    sys.exit(1)
    
sock.bind((dev_id,))

def signal_handler(signal, frame):
    err = bluez.hci_le_set_scan_enable(
        sock.fileno(),
        0,  # 1 - turn on;  0 - turn off
        0, # 0-filtering disabled, 1-filter out duplicates
        1000  # timeout
    )
    if err < 0:
        errnum = get_errno()
        raise Exception("{} {}".format(
            errno.errorcode[errnum],
            os.strerror(errnum)
        ))
    
    sock.close()
    print("Badge Summary")
    print(badges)
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

err = bluez.hci_le_set_scan_parameters(sock.fileno(), 0, 0x10, 0x10, 0, 0, 1000);
if err < 0:
    raise Exception("Set scan parameters failed")
    # occurs when scanning is still enabled from previous call

# allows LE advertising events
hci_filter = struct.pack(
    "<IQH", 
    0x00000010, 
    0x4000000000000000, 
    0
)
sock.setsockopt(SOL_HCI, HCI_FILTER, hci_filter)

err = bluez.hci_le_set_scan_enable(
    sock.fileno(),
    1,  # 1 - turn on;  0 - turn off
    0, # 0-filtering disabled, 1-filter out duplicates
    1000  # timeout
)
if err < 0:
    errnum = get_errno()
    raise Exception("{} {}".format(
        errno.errorcode[errnum],
        os.strerror(errnum)
    ))

while True:
    data = sock.recv(1024)
    badge_time = time.time()
    
    #print bluetooth address from LE Advert. packet
    #print(':'.join("{0:02x}".format(x) for x in data[12:6:-1]))
    #print raw advertising info
    #print(':'.join("{0:02x}".format(x) for x in data[44:13:-1]))
    #print("advertisement length is ", len(data))
    #print('!'.join("{0:02x}".format(x) for x in data))

    badge_address = ':'.join('{0:02x}'.format(x) for x in data[12:6:-1])

    index = 14
    badge = False
    badge_name = "not rcvd"
    badge_id = "xxxx"
    badge_year = "yyyy"
    #print("")
    while (index < len(data)-1):
        packet_len = data[index]
        packet_type = data[index+1]
        packet_payload = data[index+2:index+2+packet_len-1]
        #print("packet len %d type %d data %s" % (packet_len,packet_type,'.'.join("{0:02x}".format(x) for x in packet_payload)))
        index += packet_len+1
        if packet_type == 0x01:
            #print("Flags %02X" % int(packet_payload[0]))
            if int(packet_payload[0]) != 0x06:
                badge = False
        elif packet_type == 0x09:
            badge_name = packet_payload.decode("utf-8")
            #print("Local name = '%s'" % badge_name)
        elif packet_type == 0x19:
            if packet_payload[1] == 0x19 and packet_payload[0] == 0xDC:
                badge_year = "DC25"
                #print("DC25")
                badge = True
            else:
                #print("Unknown appearance %02X%02X" % (packet_payload[1], packet_payload[0]))
                badge = False
        elif packet_type == 0xFF:
            if packet_payload[1] == 0x04 and packet_payload[0] == 0x9e:
                badge_id = "%02X%02X" % (packet_payload[3],packet_payload[2])
                #print("AND!XOR Badge id=0x%s" % badge_id)
           # else:
           #    print("Manufacturer Specific Data Mfg=%02X%02X Len=%d %s" % (int(packet_payload[1]), int(packet_payload[0]), packet_len-3,'.'.join("{0:02x}".format(x) for x in packet_payload[2:])))
        #else:
        #    print("Unknown advertising type %02d" % packet_type)

    if badge:
        print("Badge %s %s %s %s %f" % (badge_year, badge_id, badge_address, badge_name, badge_time))
        if badge_address not in badges:
            badges[badge_address] = {
                BADGE_ID_NOW: badge_id,
                BADGE_IDS: [badge_id],
                BADGE_NAME_NOW: badge_name,
                BADGE_NAMES: [badge_name],
                BADGE_YEAR_NOW: badge_year,
                BADGE_YEARS: [badge_year],
                BADGE_TIME: badge_time,
                BADGE_CNT: 1,
                }
        else:
            badges[badge_address][BADGE_CNT] += 1
            badges[badge_address][BADGE_TIME] = badge_time
            badges[badge_address][BADGE_ID_NOW] = badge_id
            badges[badge_address][BADGE_NAME_NOW] = badge_name
            badges[badge_address][BADGE_YEAR_NOW] = badge_year
            if badge_name not in badges[badge_address][BADGE_NAMES]:
                badges[badge_address][BADGE_NAMES].append(badge_name)
            if badge_id not in badges[badge_address][BADGE_IDS]:
                badges[badge_address][BADGE_IDS].append(badge_id)
            if badge_year not in badges[badge_address][BADGE_YEARS]:
                badges[badge_address][BADGE_YEARS].append(badge_year)
