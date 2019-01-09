#!/usr/bin/python2
# check host network status
import __init__
import commonds

def system_call(cmd):
	status, output = commands.getstatusoutput(cmd)
	print status 
	print output
	return status, output


if __name__ == '__main__':
	system_call()