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
networks_info = get_project_network_info(auth_token, auth_url, endpoint_url)
# # print get_port_network_info(network_info['ports'][0], network_info)
# from libvirt_func import get_vm_port_netinfo, get_vm_port_netstats, get_nic_netstats
# # print get_vm_port_netinfo()
# vm_port_netstats = get_vm_port_netstats()
# get_nic_netstats()

from novaclient import client as nvclient
from openstackapi.auth import get_token
auth_url = 'http://192.168.122.9:5000/v3'
username = 'admin'
password = 'e60ed34c828d44b9'
project_name = 'admin'
auth_token = get_token(username, password, auth_url, project_name)
from openstackapi.nova import get_project_server_info
vms_info = get_project_server_info(auth_token, auth_url, project_name)

# topo = {
# 		"device": [],
# 		"tap":[],
# 		"qbr":[],
# 		"qvb":[],
# 		"qvo":[],
# 		"br-int-port":[],
# 		"br-int":[],
# 		"ovs-provider":[],
# 		"nic":[],
# 		"physical-switch":[]
# 		}
# touch_ips = set()
# from func import get_vm_topo
# for vm in vm_info:
# 	get_vm_topo(vm, network_info, topo, touch_ips, vm_port_netstats)

# print topo
# print topo['device']
# from func import get_network_topo
# get_network_topo(network_info, topo, touch_ips)
# print topo
# from func import get_network_from_ip
# print get_network_from_ip("192.168.122.1/24")
from func import get_nic_ex_info, get_nic_tun_ip, get_nic_tun_info, get_tunnel_remote
# info = {}
# get_nic_ex_info(info)
# print info
# ip = get_nic_tun_ip()
# info = {'ip_address': ip[1]}
# print get_nic_tun_info(info)
# from ovs.bridge import get_ovs_info
# ret, br_info = get_ovs_info()
# print get_tunnel_remote(br_info['br-tun'])
from func import get_topo
from libvirt_func import get_vm_info_in_host
vm_info_in_host = get_vm_info_in_host()
vm_info = []
for vm in vms_info:
	if vm['id'] in vm_info_in_host:
		vm_info.append(vm)
ret, topo = get_topo(vm_info, networks_info)
# print topo
# from func import process_tap_info
# from func import exe
# ret, info = exe("ip addr show %s" %("tap879f22e7-61"))
# print process_tap_info(info)
# ret, info = exe("ip addr show %s" %("br-ex"))
# print process_tap_info(info)
from func import check_br_int_port, get_bridge_info, get_all_ns, check_ns_exist, check_network_device
# check_br_int_port(topo['br-int-port'][0], topo)
# print get_bridge_info('qbr3ef787ad-67')
# print get_all_ns()
#print check_ns_exist('qrouter-92e27a1f-2330-4444-a2bd-2fdab1d18504')
#print check_ns_exist('qrouter-92e27a1f-2330-4444-a2bd-2fdab1d1851')
# print len(topo['device'])
# for i in topo['device']:
# 	print i['name']
# from func import check_network_ovs
from func import check_network_nic, check_network_config, get_test_ip
# check_network_device(topo)
# check_network_ovs(topo)
# check_network_nic(topo)

check_network_config(topo)

# print get_test_ip("192.168.122.3", 24)
from func import create_netns, create_ovs_port, set_tap_to_netns
# print create_netns("test")
# create_ovs_port('br-int', 'test', '1')
# set_tap_to_netns('test', 'test')
from func import bond_tap_addr, ping_test
# print bond_tap_addr('test', 'test', '192.168.1.10/24')
# print ping_test('192.168.1.8', 'test')

from func import is_connect_internal, check_device_connection, check_nic_connection, check_network_connection
# print is_connect_internal('1234567890123','192.168.1.8', '24', '1')
# check_device_connection(topo['device'][0], topo)
# check_nic_connection(topo['nic'][0], topo)
check_network_connection(topo)

#openstack image create "centos-7"   --file CentOS-7-x86_64-Azure2.qcow2  --disk-format qcow2 --container-format bare  --public


