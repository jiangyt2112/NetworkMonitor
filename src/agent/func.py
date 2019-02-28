#!/usr/bin/python2
import __init__
import commands
import libvirt
import libxml2
import json
# 61205745-b2bf-4db0-ad50-e7a60bf08bd5
# 61205745-b2bf-4db0-ad50-e7a60bf08bd5

def exe(cmd):
	return commands.getstatusoutput(cmd)  

def get_vm_uuids():
	# get all vm uuid in the host
	uuids = set()
	conn = libvirt.openReadOnly(None)

	if conn is None:
	    return False, 'Failed to open connection to the hypervisor'
	else:
	    doms = conn.listAllDomains()
	    for dom in doms:
	        uuids.add(dom.UUIDString())
	    return True, uuids

def get_host_ip():
	ret, ips = exe('ifconfig -a|grep inet|grep -v 127.0.0.1|grep -v inet6|awk '{print $2}'|tr -d "addr:"')
	if ret == False:
		return False, None
	return True, ips.split()

if __name__ == '__main__':
	print get_vm_uuids()
	print get_host_ip()
	    