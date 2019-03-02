#!/usr/bin/python2
from ovs import bridge
br = Bridge()

if __name__ == '__main__':
    print br.show_br()