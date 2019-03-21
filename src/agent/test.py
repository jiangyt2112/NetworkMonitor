#!/usr/bin/python2
import __init__
from func import exe
from func import get_bridge_info
from func import ping_test
from func import get_nic_info
# info = exe("ip netns exec qrouter-d4edac45-231a-4b5e-9e95-c629d5c7fc62 ip addr show qg-b8cfeaad-ef")
# info = info[1]
# print process_tap_info(info)

# print get_bridge_info("qbr3ef787ad-67")

# print get_bridge_info("qbr3ef787ad-68")
# print ping_test("192.168.166.1", "")
# print ping_test("192.168.166.2", "")
# print get_nic_info("br-ex")
# print get_nic_info("ens5")

try:
    import psutil
except ImportError:
    print('Error: psutil module not found!')
    exit()


def get_key():
 
    key_info = psutil.net_io_counters(pernic=True).keys()
 
    recv = {}
    sent = {}
 
    for key in key_info:
        recv.setdefault(key, psutil.net_io_counters(pernic=True).get(key).bytes_recv)
        sent.setdefault(key, psutil.net_io_counters(pernic=True).get(key).bytes_sent)
 
    return key_info, recv, sent


def get_rate(func):
 
    import time
 
    key_info, old_recv, old_sent = func()
 
    time.sleep(1)
 
    key_info, now_recv, now_sent = func()
    net_in = {}
    net_out = {}
 
    for key in key_info:
        net_in.setdefault(key, (now_recv.get(key) - old_recv.get(key)) / 1024)
        net_out.setdefault(key, (now_sent.get(key) - old_sent.get(key)) / 1024)
 
    return key_info, net_in, net_out
 
while 1:
    try:
         key_info, net_in, net_out = get_rate(get_key)
 
         for key in key_info:
             print('%s\nInput:\t %-5sKB/s\nOutput:\t %-5sKB/s\n' % (key, net_in.get(key), net_out.get(key)))
    except KeyboardInterrupt:
        exit()