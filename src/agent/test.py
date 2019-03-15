#!/usr/bin/python2
import __init__
from func import exe
from func import get_bridge_info
# info = exe("ip netns exec qrouter-d4edac45-231a-4b5e-9e95-c629d5c7fc62 ip addr show qg-b8cfeaad-ef")
# info = info[1]
# print process_tap_info(info)

print get_bridge_info("qbr3ef787ad-67")

print get_bridge_info("qbr3ef787ad-68")