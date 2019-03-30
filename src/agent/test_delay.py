#!/usr/bin/python2
import ping
import sys

print ping.quiet_ping(sys.argv[1])
sys.exit(0)