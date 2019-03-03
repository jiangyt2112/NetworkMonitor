#!/usr/bin/python2
import __init__
import commands
import libvirt
import libxml2
import json
from ovs.bridge import Bridge
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

def get_hostname():
	ret, name = exe('hostname')
	if ret != 0:
		return false, name
	return True, name

def get_host_ip():
	ret, ips = exe('ifconfig -a|grep inet|grep -v 127.0.0.1|grep -v inet6|awk \'{print $2}\'|tr -d "addr:"')
	if ret != 0:
		return False, ips
	return True, ips.split()

def is_network_node():
	ret, info = exe('systemctl status neutron-server.service')
	if ret == 0:
		return True
	return False

def get_topo():
	pass
	return True, None


def get_bridge():
	br = Bridge()
	return br.show_br()

def check_service(service):
	ret, result = exe("systemctl status %s" %(service))
	if ret == False:
		return False, None
	status = result.split("\n").split()[1]
	if status == "active":
		return True, True
	else:
		return True, False

if __name__ == '__main__':
	# print get_vm_uuids()
	# print get_host_ip()
	# print is_network_node()
	print check_service("openstack-nova-compute")
	    