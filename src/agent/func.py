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
	ret, result = commands.getstatusoutput(cmd)
	if ret == 0:
		return True, result
	else:
		return False, result

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
	if not ret:
		return false, name
	return True, name

def get_host_ip():
	ret, ips = exe('ifconfig -a|grep inet|grep -v 127.0.0.1|grep -v inet6|awk \'{print $2}\'|tr -d "addr:"')
	if not ret:
		return False, ips
	return True, ips.split()

def is_network_node():
	ret, info = exe('systemctl status neutron-server.service')
	if ret == 0:
		return True, None
	return False, info

def get_vm_topo(vm_info, networks_info, topo, touch_ips):
	# vm level
	vm = {
		'id': vm_info['id'],
		'status': vm_info['status'],
		'host': vm_info['OS-EXT-SRV-ATTR:host'],
		'name': vm_info['name'],
		'created': vm_info['created'],
		'addresses': {}
		'type': "virtual host",
		'check': {"result": None, "error_msg": ""},
		'performance': None,
		'next': []
	}

	for addr in vm_info["addresses"]:
		nets = vm_info["addresses"][addr]
		vm["addresses"][addr] = []
		for i in nets:
			vm["addresses"][addr].append(
				{
					"mac_addr": i['OS-EXT-IPS-MAC:mac_addr'],
					"version": i['version'],
					'addr': i['addr'],
					'type': i['OS-EXT-IPS:type']
				}
			)

	topo['device'].append(vm)

	# tap level
	vm_fixed_ips_set = set()
	for net_name in vm["addresses"]:
		for ip_addr in vm["addresses"][net_name]:
			if ip_addr['type'] == 'fixed':
				touch_ips.add(ip_addr['addr'])
				vm_fixed_ips_set.add(ip_addr['addr'])
	
	tap_num = 0
	tap_index = len(topo['tap'])
	for port in networks_info["ports"]:
		if port['fixed_ips']['ip_address'] in vm_fixed_ips_set:
			
			tap_info = {}
			tap_info['id'] = port['id']
			tap_info['name'] = "tap" + port['id'][:11]
			tap_info['mac_addr'] = port['mac_addr']
			tap_info['status'] = port['status']
			tap_info['addresses'] = []
			tap_info['type'] = "tap device"
			tap_info['check'] = {"result": None, "error_msg": ""}
			tap_info['next'] = len(topo['qbr']) + tap_num
			topo['tap'].append(tap_info)
			vm['next'].append(len(topo['tap']) - 1)
			tap_num += 1


	# qbr qvb qvo br-int
	for i in range(tap_num):
		qbr_info = {}
		id11 = topo['tap'][tap_index + i]['id'][:11]
		qbr_info['name'] = "qbr" + id11
		qbr_info['interfaces'] = ["qvb" + id11, "tap" + id11]
		qbr_info['type'] = "linux bridge"
		qbr_info['check'] = {"result": None, "error_msg": ""}
		qbr_info['next'] = len(topo['qvb'])
		topo['qbr'].append(qbr_info)

		qvb_info = {}
		qvb_info['name'] = "qvb" + id11 + '@' + "qvo" + id11
		qvb_info['master'] = qbr_info['name']
		qvb_info['type'] = "veth device"
		qvb_info['check'] = {"result": None, "error_msg": ""}
		qvb_info['next'] = len(topo['qvo'])
		topo['qvb'].append(qvb_info)

		qvo_info = {}
		qvo_info['name'] = "qvo" + id11 + '@' + "qvb" + id11
		qvo_info['master'] = 'ovs-system'
		qvo_info['type'] = "veth device"
		qvo_info['check'] = {"result": None, "error_msg": ""}
		qvo_info['next'] = len(topo['br-int-port'])
		topo['qvo'].append(qvo_info)

		br_int_port_info = {}
		br_int_port_info['name'] = "qvo" + id11
		br_int_port_info['tag'] = None
		br_int_port_info['interface'] = br_int_info['name']
		br_int_port_info['type'] = "ovs bridge port"
		br_int_port_info['check'] = {"result": None, "error_msg": ""}
		br_int_port_info['next'] = 0
		topo['br-int-port'].append(br_int_port_info)

def is_same_net(qg_info, port):
	for addr in qg_info['addresses']:
		if port['fixed_ips'][0]['subnet_id'] == addr['subnet_id']:
			return True
	return False


def get_network_top(networks_info, topo, touch_ips):
	# dhcp
	for port in networks_info["port"]:
		if port['device_owner'] == 'network:dhcp':
			dhcp_info = {}
			#dhcp_info['id'] = port['id']
			dhcp_info['netns'] = "qdhcp-" + port['network_id']
			dhcp_info['created_at'] = port['created_at']
			dhcp_info['type'] = "dhcp"
			dhcp_info['status'] = None
			dhcp_info['check'] = {"result": None, "error_msg": ""}
			dhcp_info['next'] = len(topo['tap'])
			topo['device'].append(dhcp_info)

			tap_info = {}
			tap_info['id'] = port['id']
			tap_info['name'] = "tap" + port['id'][:11]
			tap_info['mac_addr'] = port['mac_addr']
			tap_info['status'] = port['status']
			tap_info['addresses'] = []
			for i in port['fixed_ips']:
			 	tap_info['addresses'].append(i)
			tap_info['type'] = "tap device"
			tap_info['check'] = {"result": None, "error_msg": ""}
			tap_info['next'] = len(topo['qbr'])
			topo['tap'].append(tap_info)

			qbr_info = {}
			#id11 = topo['tap'][tap_index + i]['id'][:11]
			qbr_info['name'] = ""
			qbr_info['interfaces'] = ""
			qbr_info['type'] = "placeholder"
			qbr_info['check'] = {"result": None, "error_msg": ""}
			qbr_info['next'] = len(topo['qvb'])
			topo['qbr'].append(qbr_info)

			qvb_info = {}
			qvb_info['name'] = ""
			qvb_info['master'] = ""
			qvb_info['type'] = "placeholder"
			qvb_info['check'] = {"result": None, "error_msg": ""}
			qvb_info['next'] = len(topo['qvo'])
			topo['qvb'].append(qvb_info)

			qvo_info = {}
			qvo_info['name'] = ""
			qvo_info['master'] = ''
			qvo_info['type'] = "placeholder"
			qvo_info['check'] = {"result": None, "error_msg": ""}
			qvo_info['next'] = len(topo['br-int-port'])
			topo['qvo'].append(qvo_info)

			br_int_port_info = {}
			br_int_port_info['name'] = "tap" + port['id'][:11]
			br_int_port_info['tag'] = None
			br_int_port_info['interface'] = br_int_info['name']
			br_int_port_info['type'] = "ovs bridge port"
			br_int_port_info['check'] = {"result": None, "error_msg": ""}
			br_int_port_info['next'] = 0
			topo['br-int-port'].append(br_int_port_info)

	for r in networks_info['routers']:
		router_info = {}
		router_info['id'] = r['id']
		router_info['name'] = r['name']
		router_info['namespaces'] = "qrouter-" + r['id']
		router_info['status'] = r['status']
		router_info['check'] = {"result": None, "error_msg": ""}
		router_info['next'] = []
		# qr qg
		
		for port in networks_info['port']:
			if port['device_id'] == router_info['id']:
				router_info['next'].append(len(topo['tap']))
				q_info = {}
				q_info['id'] = port['id']
				if port['device_owner'] == 'network:router_interface':
					q_info['name'] = "qr" + port['id'][:11]
				else:
					q_info['name'] = "qg" + port['id'][:11]
				q_info['mac_addr'] = port['mac_addr']
				q_info['status'] = port['status']
				q_info['addresses'] = []
				for i in port['fixed_ips']:
				 	q_info['addresses'].append(i)
				q_info['type'] = "ovs internal"
				q_info['check'] = {"result": None, "error_msg": ""}
				q_info['next'] = len(topo['qbr'])
				router_info['next'] = len(topo['tap'])
				topo['tap'].append(q_info)

				qbr_info = {}
				#id11 = topo['tap'][tap_index + i]['id'][:11]
				qbr_info['name'] = ""
				qbr_info['interfaces'] = ""
				qbr_info['type'] = "placeholder"
				qbr_info['check'] = {"result": None, "error_msg": ""}
				qbr_info['next'] = len(topo['qvb'])
				topo['qbr'].append(qbr_info)

				qvb_info = {}
				qvb_info['name'] = ""
				qvb_info['master'] = ""
				qvb_info['type'] = "placeholder"
				qvb_info['check'] = {"result": None, "error_msg": ""}
				qvb_info['next'] = len(topo['qvo'])
				topo['qvb'].append(qvb_info)

				qvo_info = {}
				qvo_info['name'] = ""
				qvo_info['master'] = ''
				qvo_info['type'] = "placeholder"
				qvo_info['check'] = {"result": None, "error_msg": ""}
				qvo_info['next'] = len(topo['br-int-port'])
				topo['qvo'].append(qvo_info)

				br_int_port_info = {}
				br_int_port_info['name'] = q_info['name']
				br_int_port_info['tag'] = None
				br_int_port_info['interface'] = br_int_info['name']
				br_int_port_info['type'] = "internal"
				br_int_port_info['check'] = {"result": None, "error_msg": ""}
				br_int_port_info['next'] = 0
				topo['br-int-port'].append(br_int_port_info)

				
	for port in networks_info['port']:
		if port['device_owner'] == 'network:floatingip':
			for t in topo['tap']:
				if t['type'] == "ovs internal" and is_same_net(t, port):
					t['addresses'].append(
						{'subnet_id': port['addresses'][0]['subnet_id'],
						'ip_address': port['addresses'][0]['ip_address'],
						'type': 'floatingip'
						})


def get_network_from_ip(ip):
	# 192.168.166.9/24
	addr = ip.slit('/')[0].split('.')
	mask = int(ip.slit('/')[1])
	temp_mask = mask
	for i in range(len(addr)):
		addr[i] = int(addr[i])
	index = len(addr) - 1
	while mask >= 8:
		addr[index] = 0
		index -= 1
		mask -= 8
	if mask != 0:
		addr[index] /= pow(2, mask)
		addr[index] *= pow(2, mask)

	ret_ip = ""
	for i in range(len(addr)):
		if i != 0:
			ret_ip += '.'
		ret_ip += addr[i]
	ret_ip += "/" + str(mask)
	return ret_ip

def get_nic_ex_info(nic_ex_info):
	# nic_ex_info = {}
	# nic_ex_info['name'] = ""
	# nic_ex_info['device'] = ""
	# nic_ex_info['physical_device'] = ""
	# nic_ex_info['ip_address'] = ""
	# nic_ex_info['type'] = "ovs bridge"
	# nic_ex_info['check'] = {"result": None, "error_msg": ""}
	ret, result = exe("ip address | grep br-ex")
	if ret == False:
		return ret, result
	nic_ex_info['ip_address'] = result.split('\n')[1].split()[1]
	br = Bridge()
	for pd in br['br-ex']['Port']:
		if pd != "br-ex" and pd != "phy-br-ex":
			nic_ex_info['physical_device'] = pd
	return True, None

def get_nic_tun_ip():


def get_nic_tun_info():

def get_topo(vms_info, networks_info):
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

	for vm in vms_info:
		get_vm_topo(vm, networks_info, topo, touch_ips)

	get_network_top(networks_info, topo, touch_ips)

	br = Bridge()
	if br == {}:
		return False, "get ovs bridge info error."
	br_int_info = br['br-int']
	br_int_info['type'] = "ovs bridge"
	br_int_info['check'] = {"result": None, "error_msg": ""}
	br_int_info['next'] = [0]
	topo['br-int'].append(br_int_info)
	br_tun_info = br['br-tun']
	br_tun_info['type'] = "ovs bridge"
	br_tun_info['check'] = {"result": None, "error_msg": ""}
	br_tun_info['next'] = [0]
	topo['br-provider'].append(br_tun_info)
	if 'br-ex' in br:
		br_int_info['next'].append(1)
		br_ex_info = br['br-ex']
		br_ex_info['type'] = "ovs bridge"
		br_ex_info['check'] = {"result": None, "error_msg": ""}
		br_ex_info['next'] = [1]
		topo['br-provider'].append(br_ex_info)

	nic_ex_info = {}
	nic_ex_info['name'] = ""
	nic_ex_info['device'] = ""
	nic_ex_info['physical_device'] = ""
	nic_ex_info['ip_address'] = ""
	nic_ex_info['type'] = "ovs bridge"
	nic_ex_info['check'] = {"result": None, "error_msg": ""}
	nic_ex_info['next'] = [1]
	ret, error_msg = get_nic_ex_info(nic_ex_info)
	if ret == False:
		return ret, error_msg

	nic_tun_ip = get_nic_tun_ip()
	if nic_tun_ip == nic_ex_info['ip_address']
		topo['nic'].append(nic_ex_info)
		nic_ex_info['next'] = 0
		if 'br-ex' in br:
			br_ex_info['next'] = 0
		physical_switch_info = {}
		physical_switch_info['type'] = 'physical switch'
		physical_switch_info['network'] = get_network_from_ip(nic_ex_info['ip_address'])
		physical_switch_info['name'] = "physical switch " + physical_switch_info['network']
		physical_switch_info['check'] = {"result": None, "error_msg": ""}
		physical_switch_info['next'] = None
		topo['physical-switch'].append(physical_switch_info)
	else:
		nic_tun_info = {}
		nic_tun_info['name'] = ""
		nic_tun_info['device'] = ""
		nic_tun_info['physical_device'] = ""
		nic_tun_info['ip_address'] = ""
		nic_tun_info['type'] = "ovs bridge"
		nic_tun_info['check'] = {"result": None, "error_msg": ""}
		nic_tun_info['next'] = [0]
		get_nic_tun_info(nic_tun_info)
		topo['nic'].append(nic_tun)
		topo['nic'].append(nic_ex)

		physical_switch_tun_info = {}
		physical_switch_tun_info['type'] = 'physical switch'
		physical_switch_tun_info['network'] = get_network_from_ip(nic_tun_info['ip_address'])
		physical_switch_tun_info['name'] = "physical switch " + physical_switch_tun_info['network']
		physical_switch_tun_info['check'] = {"result": None, "error_msg": ""}
		physical_switch_tun_info['next'] = None
		topo['physical-switch'].append(physical_switch_tun_info)

		physical_switch_ex_info = {}
		physical_switch_ex_info['type'] = 'physical switch'
		physical_switch_ex_info['network'] = get_network_from_ip(nic_ex_info['ip_address'])
		physical_switch_ex_info['name'] = "physical switch " + physical_switch_ex_info['network']
		physical_switch_ex_info['check'] = {"result": None, "error_msg": ""}
		physical_switch_ex_info['next'] = None
		topo['physical-switch'].append(physical_switch_ex_info)
		
	return True, topo


def get_bridge():
	br = Bridge()
	return br.show_br()

def check_service(service):
	ret, result = exe("systemctl status %s" %(service))
	if not ret:
		return False, None
	status = result.split("\n")[2].split()[1]
	if status == "active":
		return True, True
	else:
		return True, False

if __name__ == '__main__':
	# print get_vm_uuids()
	# print get_host_ip()
	# print is_network_node()
	print check_service("openstack-nova-compute")
	    