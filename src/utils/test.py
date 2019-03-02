#!/usr/bin/python2
import __init__
from ovs.bridge import Bridge
br = Bridge()

if __name__ == '__main__':
    print br.show_br()