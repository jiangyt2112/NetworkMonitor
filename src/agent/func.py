#!/usr/bin/python2
import __init__
import commands
import libvirt
import libxml2
import json
from ovs.bridge import get_ovs_info
from utils.log import AGENTLOG
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
	if not ret:
		return False, 'is_network_node test error.'

	if info.split("\n")[2].strip().split(' ')[1] == 'active':
		return True, True
	else:
		return True, False

def get_vm_topo(vm_info, networks_info, topo, touch_ips):
	# vm level
	vm = {
		'id': vm_info['id'],
		'status': vm_info['status'],
		'host': vm_info['OS-EXT-SRV-ATTR:host'],
		'name': vm_info['name'],
		'created': vm_info['created'],
		'addresses': {},
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
		if port['fixed_ips'][0]['ip_address'] in vm_fixed_ips_set:
			
			tap_info = {}
			tap_info['id'] = port['id']
			tap_info['name'] = "tap" + port['id'][:11]
			tap_info['mac_address'] = port['mac_address']
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
		br_int_port_info['interface'] = br_int_port_info['name']
		br_int_port_info['type'] = "ovs bridge port"
		br_int_port_info['check'] = {"result": None, "error_msg": ""}
		br_int_port_info['next'] = 0
		topo['br-int-port'].append(br_int_port_info)

def is_same_net(qg_info, port):
	for addr in qg_info['addresses']:
		if port['fixed_ips'][0]['subnet_id'] == addr['subnet_id']:
			return True
	return False


def get_network_topo(networks_info, topo, touch_ips):
	# dhcp
	for port in networks_info["ports"]:
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
			tap_info['mac_address'] = port['mac_address']
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
			br_int_port_info['interface'] = br_int_port_info['name']
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
		
		for port in networks_info['ports']:
			if port['device_id'] == router_info['id']:
				print router_info['next']
				#router_info['next'].append(len(topo['tap']))
				q_info = {}
				q_info['id'] = port['id']
				if port['device_owner'] == 'network:router_interface':
					q_info['name'] = "qr" + port['id'][:11]
				else:
					q_info['name'] = "qg" + port['id'][:11]
				q_info['mac_address'] = port['mac_address']
				q_info['status'] = port['status']
				q_info['addresses'] = []
				for i in port['fixed_ips']:
				 	q_info['addresses'].append(i)
				q_info['type'] = "ovs internal"
				q_info['check'] = {"result": None, "error_msg": ""}
				q_info['next'] = len(topo['qbr'])
				router_info['next'].append(len(topo['tap']))
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
				br_int_port_info['interface'] = br_int_port_info['name']
				br_int_port_info['type'] = "internal"
				br_int_port_info['check'] = {"result": None, "error_msg": ""}
				br_int_port_info['next'] = 0
				topo['br-int-port'].append(br_int_port_info)

				
	for port in networks_info['ports']:
		if port['device_owner'] == 'network:floatingip':
			for t in topo['tap']:
				if t['type'] == "ovs internal" and is_same_net(t, port):
					t['addresses'].append(
						{'subnet_id': port['fixed_ips'][0]['subnet_id'],
						'ip_address': port['fixed_ips'][0]['ip_address'],
						'type': 'floatingip'
						})


def get_network_from_ip(ip):
	# 192.168.166.9/24
	addr = ip.split('/')[0].split('.')
	mask = int(ip.split('/')[1])
	temp_mask = mask
	mask = 32 - mask
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
		ret_ip += str(addr[i])
	ret_ip += "/" + str(temp_mask)
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
	
	ret, br_info = get_ovs_info()
	if ret == False:
		return ret, br_info

	for pd in br_info['br-ex']['Port']:
		if pd != "br-ex" and pd != "phy-br-ex":
			nic_ex_info['physical_device'] = pd
	return True, None

def get_nic_tun_ip():
	ret, result = exe('ovs-vsctl show | grep "local_ip"')
	if ret == False:
		return ret, result

	start = result.find("local_ip")
	left = result.find("\"", start)
	right = result.find("\"", left + 1)
	tun_ip = result[left + 1: right]

	ret, result = exe('ip a | grep ' + tun_ip)
	if ret == False:
		return ret, result

	return True, result.strip().split(' ')[1]


def get_nic_tun_info(nic_tun_info):
	# nic_tun_info = {}
	tun_ip = nic_tun_info['ip_address']
	ret, result = exe('ip a | grep ' + tun_ip)
	if ret == False:
		return ret, result
	nic_tun_info['name'] = result.strip().split(' ')[-1]
	nic_tun_info['device'] = nic_tun_info['name']
	nic_tun_info['physical_device'] = nic_tun_info['name']
	return True, nic_tun_info

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

	AGENTLOG.info("agent.func.get_topo -  get vm topo start.")
	for vm in vms_info:
		get_vm_topo(vm, networks_info, topo, touch_ips)
	AGENTLOG.info("agent.func.get_topo -  get vm topo done.")


	AGENTLOG.info("agent.func.get_topo -  get network topo start.")
	get_network_topo(networks_info, topo, touch_ips)
	AGENTLOG.info("agent.func.get_topo -  get network topo done.")

	AGENTLOG.info("agent.func.get_topo -  get ovs info start.")

	ret, br_info = get_ovs_info()
	if ret == False:
		return False, "get ovs bridge info error."
	
	AGENTLOG.info("agent.func.get_topo -  get ovs info done.")


	br_int_info = br_info['br-int']
	br_int_info['type'] = "ovs bridge"
	br_int_info['check'] = {"result": None, "error_msg": ""}
	br_int_info['next'] = [0]
	topo['br-int'].append(br_int_info)
	br_tun_info = br_info['br-tun']
	br_tun_info['type'] = "ovs bridge"
	br_tun_info['check'] = {"result": None, "error_msg": ""}
	br_tun_info['next'] = [0]
	topo['ovs-provider'].append(br_tun_info)
	if 'br-ex' in br_info:
		br_int_info['next'].append(1)
		br_ex_info = br_info['br-ex']
		br_ex_info['type'] = "ovs bridge"
		br_ex_info['check'] = {"result": None, "error_msg": ""}
		br_ex_info['next'] = [1]
		topo['ovs-provider'].append(br_ex_info)

	nic_ex_info = {}
	nic_ex_info['name'] = ""
	nic_ex_info['device'] = ""
	nic_ex_info['physical_device'] = ""
	nic_ex_info['ip_address'] = ""
	nic_ex_info['type'] = "ovs bridge"
	nic_ex_info['check'] = {"result": None, "error_msg": ""}
	nic_ex_info['next'] = [1]

	AGENTLOG.info("agent.func.get_topo -  get_nic_ex_info start.")
	ret, error_msg = get_nic_ex_info(nic_ex_info)
	if ret == False:
		return ret, error_msg
	AGENTLOG.info("agent.func.get_topo -  get_nic_ex_info done.")

	AGENTLOG.info("agent.func.get_topo -  get_nic_tun_ip start.")
	ret, nic_tun_ip = get_nic_tun_ip()
	if ret == False:
		return ret, nic_tun_ip
	AGENTLOG.info("agent.func.get_topo -  get_nic_tun_ip done.")

	if nic_tun_ip == nic_ex_info['ip_address']:
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
		nic_tun_info['ip_address'] = nic_tun_ip
		nic_tun_info['type'] = "interface"
		nic_tun_info['check'] = {"result": None, "error_msg": ""}
		nic_tun_info['next'] = [0]

		AGENTLOG.info("agent.func.get_topo -  get_nic_tun_info start.")
		ret, result = get_nic_tun_info(nic_tun_info)
		if ret == False:
			return ret, result
		AGENTLOG.info("agent.func.get_topo -  get_nic_tun_info done.")

		topo['nic'].append(nic_tun_info)
		topo['nic'].append(nic_ex_info)

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
	# print check_service("openstack-nova-compute")
	# print is_network_node()
	valid_vm_info = [{u'status': u'ACTIVE', u'updated': u'2019-03-04T01:31:34Z', u'OS-EXT-STS:task_state': None, u'user_id': u'd2fcc0c45a134de28dba429dbef2c3ba', u'addresses': {u'int-net': [{u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:0e:ab:01', u'version': 4, u'addr': u'192.168.1.4', u'OS-EXT-IPS:type': u'fixed'}, {u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:0e:ab:01', u'version': 4, u'addr': u'192.168.166.26', u'OS-EXT-IPS:type': u'floating'}]}, u'created': u'2019-03-04T01:31:25Z', u'OS-SRV-USG:terminated_at': None, u'tenant_id': u'a95424bbdca6410092073d564f1f4012', u'hostId': u'1b6fa73a7ea8e40dc812954fe751d3aa812e6b52489ddb5360f5d36e', u'OS-EXT-SRV-ATTR:host': u'control-node', u'OS-EXT-STS:vm_state': u'active', u'OS-EXT-SRV-ATTR:instance_name': u'instance-00000003', u'progress': 0, u'OS-SRV-USG:launched_at': u'2019-03-04T01:31:34.000000', u'OS-EXT-SRV-ATTR:hypervisor_hostname': u'control-node', u'OS-EXT-STS:power_state': 1, u'OS-EXT-AZ:availability_zone': u'nova', u'id': u'6d4f4a19-d581-492f-92fd-88f56cc85767', u'security_groups': [{u'name': u'default'}], u'name': u'test1'}, {u'status': u'ACTIVE', u'updated': u'2019-02-28T08:38:58Z', u'OS-EXT-STS:task_state': None, u'user_id': u'd2fcc0c45a134de28dba429dbef2c3ba', u'addresses': {u'int-net': [{u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:5d:9e:22', u'version': 4, u'addr': u'192.168.1.8', u'OS-EXT-IPS:type': u'fixed'}, {u'OS-EXT-IPS-MAC:mac_addr': u'fa:16:3e:5d:9e:22', u'version': 4, u'addr': u'192.168.166.23', u'OS-EXT-IPS:type': u'floating'}]}, u'created': u'2018-10-26T09:36:38Z', u'OS-SRV-USG:terminated_at': None, u'tenant_id': u'a95424bbdca6410092073d564f1f4012', u'hostId': u'1b6fa73a7ea8e40dc812954fe751d3aa812e6b52489ddb5360f5d36e', u'OS-EXT-SRV-ATTR:host': u'control-node', u'OS-EXT-STS:vm_state': u'active', u'OS-EXT-SRV-ATTR:instance_name': u'instance-00000002', u'progress': 0, u'OS-SRV-USG:launched_at': u'2018-10-26T09:36:46.000000', u'OS-EXT-SRV-ATTR:hypervisor_hostname': u'control-node', u'OS-EXT-STS:power_state': 1, u'OS-EXT-AZ:availability_zone': u'nova', u'id': u'61205745-b2bf-4db0-ad50-e7a60bf08bd5', u'security_groups': [{u'name': u'default'}], u'name': u'test'}]
	networks_info = {u'ports': [{u'status': u'ACTIVE', u'binding:host_id': u'control-node', u'name': u'', u'admin_state_up': True, u'network_id': u'956df7c4-25d9-4564-8b81-843462ae707a', u'tenant_id': u'a95424bbdca6410092073d564f1f4012', u'created_at': u'2018-10-26T09:33:24Z', u'updated_at': u'2018-10-26T09:33:27Z', u'binding:vnic_type': u'normal', u'binding:vif_type': u'ovs', u'device_owner': u'network:dhcp', u'mac_address': u'fa:16:3e:d0:20:d1', u'id': u'3e25711d-884a-413a-a9e3-06b4f9225117', u'port_security_enabled': False, u'project_id': u'a95424bbdca6410092073d564f1f4012', u'fixed_ips': [{u'subnet_id': u'3761ef2d-d30c-46b4-8d03-ae38c411ab5b', u'ip_address': u'192.168.1.2'}], u'binding:vif_details': {u'port_filter': True, u'datapath_type': u'system', u'ovs_hybrid_plug': True}, u'device_id': u'dhcp280b4426-d1ca-5484-9f17-9aa7c0b012c5-956df7c4-25d9-4564-8b81-843462ae707a'}, {u'status': u'ACTIVE', u'binding:host_id': u'control-node', u'name': u'', u'admin_state_up': True, u'network_id': u'956df7c4-25d9-4564-8b81-843462ae707a', u'tenant_id': u'a95424bbdca6410092073d564f1f4012', u'created_at': u'2018-10-26T09:36:41Z', u'updated_at': u'2019-02-28T08:38:58Z', u'binding:vnic_type': u'normal', u'binding:vif_type': u'ovs', u'device_owner': u'compute:nova', u'mac_address': u'fa:16:3e:5d:9e:22', u'id': u'3ef787ad-6748-4b58-87a1-6af1441cc947', u'port_security_enabled': True, u'project_id': u'a95424bbdca6410092073d564f1f4012', u'fixed_ips': [{u'subnet_id': u'3761ef2d-d30c-46b4-8d03-ae38c411ab5b', u'ip_address': u'192.168.1.8'}], u'binding:vif_details': {u'port_filter': True, u'datapath_type': u'system', u'ovs_hybrid_plug': True}, u'device_id': u'61205745-b2bf-4db0-ad50-e7a60bf08bd5'}, {u'status': u'ACTIVE', u'binding:host_id': u'control-node', u'name': u'', u'admin_state_up': True, u'network_id': u'956df7c4-25d9-4564-8b81-843462ae707a', u'tenant_id': u'a95424bbdca6410092073d564f1f4012', u'created_at': u'2018-10-26T09:35:56Z', u'updated_at': u'2018-10-26T09:36:01Z', u'binding:vnic_type': u'normal', u'binding:vif_type': u'ovs', u'device_owner': u'network:router_interface', u'mac_address': u'fa:16:3e:84:7c:ec', u'id': u'661bb3c3-3651-40e7-9728-19c2565e2149', u'port_security_enabled': False, u'project_id': u'a95424bbdca6410092073d564f1f4012', u'fixed_ips': [{u'subnet_id': u'3761ef2d-d30c-46b4-8d03-ae38c411ab5b', u'ip_address': u'192.168.1.1'}], u'binding:vif_details': {u'port_filter': True, u'datapath_type': u'system', u'ovs_hybrid_plug': True}, u'device_id': u'd4edac45-231a-4b5e-9e95-c629d5c7fc62'}, {u'status': u'N/A', u'binding:host_id': u'', u'name': u'', u'admin_state_up': True, u'network_id': u'f89e858b-b386-47b5-b987-7a70bd72e861', u'tenant_id': u'', u'created_at': u'2019-03-04T01:33:11Z', u'updated_at': u'2019-03-04T01:33:12Z', u'binding:vnic_type': u'normal', u'binding:vif_type': u'unbound', u'device_owner': u'network:floatingip', u'mac_address': u'fa:16:3e:a0:09:9d', u'id': u'84a2548a-a8f5-4686-a55e-e591f53f170b', u'port_security_enabled': False, u'project_id': u'', u'fixed_ips': [{u'subnet_id': u'4d0f1eb6-16ef-4353-874a-0fe48b707e2a', u'ip_address': u'192.168.166.26'}], u'binding:vif_details': {}, u'device_id': u'b97a94d2-f578-4f30-befa-971513c62e93'}, {u'status': u'ACTIVE', u'binding:host_id': u'control-node', u'name': u'', u'admin_state_up': True, u'network_id': u'956df7c4-25d9-4564-8b81-843462ae707a', u'tenant_id': u'a95424bbdca6410092073d564f1f4012', u'created_at': u'2019-03-04T01:31:29Z', u'updated_at': u'2019-03-04T01:31:32Z', u'binding:vnic_type': u'normal', u'binding:vif_type': u'ovs', u'device_owner': u'compute:nova', u'mac_address': u'fa:16:3e:0e:ab:01', u'id': u'879f22e7-61d7-47da-adff-f5172f4c43af', u'port_security_enabled': True, u'project_id': u'a95424bbdca6410092073d564f1f4012', u'fixed_ips': [{u'subnet_id': u'3761ef2d-d30c-46b4-8d03-ae38c411ab5b', u'ip_address': u'192.168.1.4'}], u'binding:vif_details': {u'port_filter': True, u'datapath_type': u'system', u'ovs_hybrid_plug': True}, u'device_id': u'6d4f4a19-d581-492f-92fd-88f56cc85767'}, {u'status': u'N/A', u'binding:host_id': u'', u'name': u'', u'admin_state_up': True, u'network_id': u'f89e858b-b386-47b5-b987-7a70bd72e861', u'tenant_id': u'', u'created_at': u'2018-10-26T10:01:30Z', u'updated_at': u'2018-10-26T10:01:30Z', u'binding:vnic_type': u'normal', u'binding:vif_type': u'unbound', u'device_owner': u'network:floatingip', u'mac_address': u'fa:16:3e:c0:6c:33', u'id': u'ad4dcecc-2d8b-4021-b2f0-46cacf6917f8', u'port_security_enabled': False, u'project_id': u'', u'fixed_ips': [{u'subnet_id': u'4d0f1eb6-16ef-4353-874a-0fe48b707e2a', u'ip_address': u'192.168.166.23'}], u'binding:vif_details': {}, u'device_id': u'ff32223d-db9f-4b41-b647-5daf9aa69f82'}, {u'status': u'ACTIVE', u'binding:host_id': u'control-node', u'name': u'', u'admin_state_up': True, u'network_id': u'f89e858b-b386-47b5-b987-7a70bd72e861', u'tenant_id': u'', u'created_at': u'2018-10-26T09:35:38Z', u'updated_at': u'2018-10-26T09:35:43Z', u'binding:vnic_type': u'normal', u'binding:vif_type': u'ovs', u'device_owner': u'network:router_gateway', u'mac_address': u'fa:16:3e:4d:46:a6', u'id': u'b8cfeaad-eff1-4687-8109-3120102323c8', u'port_security_enabled': False, u'project_id': u'', u'fixed_ips': [{u'subnet_id': u'4d0f1eb6-16ef-4353-874a-0fe48b707e2a', u'ip_address': u'192.168.166.28'}], u'binding:vif_details': {u'port_filter': True, u'datapath_type': u'system', u'ovs_hybrid_plug': True}, u'device_id': u'd4edac45-231a-4b5e-9e95-c629d5c7fc62'}], u'subnets': [{u'name': u'int-sub', u'enable_dhcp': True, u'network_id': u'956df7c4-25d9-4564-8b81-843462ae707a', u'tenant_id': u'a95424bbdca6410092073d564f1f4012', u'created_at': u'2018-10-26T09:33:23Z', u'updated_at': u'2018-10-26T09:33:23Z', u'allocation_pools': [{u'start': u'192.168.1.2', u'end': u'192.168.1.254'}], u'host_routes': [], u'ip_version': 4, u'gateway_ip': u'192.168.1.1', u'cidr': u'192.168.1.0/24', u'project_id': u'a95424bbdca6410092073d564f1f4012', u'id': u'3761ef2d-d30c-46b4-8d03-ae38c411ab5b'}, {u'name': u'ext-sub', u'enable_dhcp': False, u'network_id': u'f89e858b-b386-47b5-b987-7a70bd72e861', u'tenant_id': u'a95424bbdca6410092073d564f1f4012', u'created_at': u'2018-10-26T09:35:20Z', u'updated_at': u'2018-10-26T09:35:20Z', u'allocation_pools': [{u'start': u'192.168.166.20', u'end': u'192.168.166.40'}], u'host_routes': [], u'ip_version': 4, u'gateway_ip': u'192.168.166.1', u'cidr': u'192.168.166.0/24', u'project_id': u'a95424bbdca6410092073d564f1f4012', u'id': u'4d0f1eb6-16ef-4353-874a-0fe48b707e2a'}], u'networks': [{u'status': u'ACTIVE', u'router:external': False, u'availability_zones': [u'nova'], u'name': u'int-net', u'provider:physical_network': None, u'subnets': [u'3761ef2d-d30c-46b4-8d03-ae38c411ab5b'], u'tenant_id': u'a95424bbdca6410092073d564f1f4012', u'created_at': u'2018-10-26T09:33:23Z', u'admin_state_up': True, u'updated_at': u'2018-10-26T09:33:23Z', u'provider:network_type': u'vxlan', u'project_id': u'a95424bbdca6410092073d564f1f4012', u'port_security_enabled': True, u'shared': False, u'mtu': 1450, u'id': u'956df7c4-25d9-4564-8b81-843462ae707a', u'provider:segmentation_id': 73}, {u'status': u'ACTIVE', u'router:external': True, u'availability_zones': [u'nova'], u'name': u'ext-net', u'provider:physical_network': u'extnet', u'subnets': [u'4d0f1eb6-16ef-4353-874a-0fe48b707e2a'], u'tenant_id': u'a95424bbdca6410092073d564f1f4012', u'created_at': u'2018-10-26T09:35:19Z', u'admin_state_up': True, u'updated_at': u'2018-10-26T09:35:20Z', u'provider:network_type': u'flat', u'project_id': u'a95424bbdca6410092073d564f1f4012', u'port_security_enabled': True, u'shared': True, u'mtu': 1500, u'id': u'f89e858b-b386-47b5-b987-7a70bd72e861', u'provider:segmentation_id': None}], u'routers': [{u'status': u'ACTIVE', u'external_gateway_info': {u'network_id': u'f89e858b-b386-47b5-b987-7a70bd72e861', u'enable_snat': True, u'external_fixed_ips': [{u'subnet_id': u'4d0f1eb6-16ef-4353-874a-0fe48b707e2a', u'ip_address': u'192.168.166.28'}]}, u'availability_zone_hints': [], u'availability_zones': [u'nova'], u'description': u'', u'tags': [], u'tenant_id': u'a95424bbdca6410092073d564f1f4012', u'created_at': u'2018-10-26T09:35:38Z', u'admin_state_up': True, u'distributed': False, u'updated_at': u'2018-10-26T09:35:56Z', u'project_id': u'a95424bbdca6410092073d564f1f4012', u'flavor_id': None, u'revision_number': 4, u'routes': [], u'ha': False, u'id': u'd4edac45-231a-4b5e-9e95-c629d5c7fc62', u'name': u'R'}]}
	print get_topo(valid_vm_info, networks_info)
	    