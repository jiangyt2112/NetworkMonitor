#!/usr/bin/python2
import __init__
from func import exe
from func import get_bridge_info
from func import ping_test
from func import get_nic_info
from func import get_vm_uuids, get_hostname, check_service, get_host_ip, is_network_node
from libvirt_func import get_vm_port_netinfo, get_nic_netstats

from neutronclient.v2_0 import client
from openstackapi.auth import get_token
from openstackapi.neutron import get_project_network_info

# info = exe("ip netns exec qrouter-d4edac45-231a-4b5e-9e95-c629d5c7fc62 ip addr show qg-b8cfeaad-ef")
# info = info[1]
# print process_tap_info(info)

# print get_bridge_info("qbr3ef787ad-67")

# print get_bridge_info("qbr3ef787ad-68")
# print ping_test("192.168.166.1", "")
# print ping_test("192.168.166.2", "")
# print get_nic_info("br-ex")
# print get_nic_info("ens5")
# print get_vm_port_netinfo()
# print get_nic_netstats()
# print get_vm_uuids()
# print get_hostname()
# print check_service("openvswitch")
# print check_service("opnevswitch")
# print get_host_ip()
# print is_network_node()

from func import get_port_network_info
auth_url = 'http://192.168.122.9:5000/v3'
endpoint_url = 'http://192.168.122.9:9696'
username = 'admin'
password = 'e60ed34c828d44b9'
project_name = 'admin'
auth_token = get_token(username, password, auth_url, project_name)
if auth_token == None:
	print 'auth fail.'
	exit(0)
network_info = get_project_network_info(auth_token, auth_url, endpoint_url)
# print get_port_network_info(network_info['ports'][0], network_info)
from libvirt_func import get_vm_port_netinfo, get_vm_port_netstats, get_nic_netstats
# print get_vm_port_netinfo()
vm_port_netstats = get_vm_port_netstats()
# get_nic_netstats()

from novaclient import client as nvclient
from openstackapi.auth import get_token
auth_url = 'http://192.168.122.9:5000/v3'
username = 'admin'
password = 'e60ed34c828d44b9'
project_name = 'admin'
auth_token = get_token(username, password, auth_url, project_name)
vm_info = get_project_server_info(auth_token, auth_url, project_name)

topo = {
		"device": [],
		"tap":[],
		"qbr":[],
		"qvb":[],
		"qvo":[],
		"br-int-port":[],
		"br-int":[],
		"ovs-provider":[],
		"nic":[],
		"physical-switch":[]
		}
touch_ips = set()
get_vm_topo(vm_info, network_info, topo, touch_ips, vm_port_netstats)