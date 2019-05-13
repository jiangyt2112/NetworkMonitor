#!/usr/bin/python2
import __init__
import commands
import libvirt
import libxml2
import json
from my_ovs.bridge import get_ovs_info
from utils.log import AGENTLOG
from libvirt_func import get_vm_info_in_host
from libvirt_func import get_vm_port_netstat_down
from libvirt_func import get_nic_netstats
from libvirt_func import get_vm_port_netstats
import psutil
import time
# 61205745-b2bf-4db0-ad50-e7a60bf08bd5
# 61205745-b2bf-4db0-ad50-e7a60bf08bd5
health_flag = True
function_fault = []
performance_fault = []

def get_mem_rate():
	phymem = psutil.virtual_memory()
    return phymem.percent

def get_cpu_rate():
	psutil.cpu_percent(None)
	time.sleep(1)
	return psutil.cpu_percent(None)

def add_function_fault(fault):
	health_flag = False
	if fault not in function_fault:
		print fault
		function_fault.append(fault)

def add_performace_fault(fault):
	health_flag = False
	if fault not in performance_fault:
		print fault
		performance_fault.append(fault)

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
		add_function_fault("libvirtd.service down.")
		return False, 'Failed to open connection to the hypervisor'
	else:
		doms = conn.listAllDomains()
		for dom in doms:
			uuids.add(dom.UUIDString())
		return True, uuids

def get_hostname():
	cmd = 'hostname'
	ret, name = exe(cmd)
	if not ret:
		add_function_fault("cmd:hostname return error(%s)" %(name))
		AGENTLOG.info("func.get_hostname - cmd:%s return error, %s" %(cmd, name))
		return ""
	return name

def check_service(service):
	cmd = "systemctl status %s" %(service)
	ret, result = exe(cmd)
	if not ret:
		AGENTLOG.info("func.check_service - cmd:%s return error, %s" %(cmd, result))
		return False
	status = result.split("\n")[2].split()[1]
	if status == "active":
		return True
	else:
		return False

def get_host_ip():
	cmd = 'ifconfig -a|grep inet|grep -v 127.0.0.1|grep -v inet6|awk \'{print $2}\'|tr -d "addr:"'
	ret, info = exe(cmd)
	if not ret:
		AGENTLOG.info("func.get_host_ip - cmd:%s return error, %s" %(cmd, info))
		add_function_fault("can't get host ip(%s)" %(info))
		return []
	return info.split()

def is_network_node():
	cmd = 'systemctl status neutron-server.service'
	ret, info = exe(cmd)
	if not ret:
		AGENTLOG.info("func.is_network_node - cmd:%s return error, %s" %(cmd, info))
		return False

	if info.split("\n")[2].strip().split(' ')[1] == 'active':
		return True
	else:
		return False

def get_port_network_info(port, networks_info):
	ret_info = {
		'ip_address': port['fixed_ips'][0]['ip_address'],
		'gateway_ip': None,
		'cidr': None,
		'dhcp': None,
		'dhcp_netns': None
	}

	subnet_id = port['fixed_ips'][0]['subnet_id']
	# port['fixed_ips'][0]['']
	for subnet in networks_info['subnets']:
		if subnet['id'] == subnet_id:
			ret_info['gateway_ip'] = subnet['gateway_ip']
			ret_info['cidr'] = subnet['cidr']
			
	for port in networks_info['ports']:
		if port['fixed_ips'][0]['subnet_id'] == subnet_id and port['device_owner'] == 'network:dhcp':
			ret_info['dhcp'] = port['fixed_ips'][0]['ip_address']
			ret_info['dhcp_netns'] = "qdhcp-" + port['network_id']
	return ret_info

def get_tap_addr(addr, networks_info):
	ret = {
		"ip_address": addr['ip_address'],
		'subnet_id': addr['subnet_id'],
		"cidr": None,
		"gateway_ip": None
	}
	for sub in networks_info['subnets']:
		if sub['id'] == addr['subnet_id']:
			ret['cidr'] = sub['cidr']
			ret['gateway_ip'] = sub['gateway_ip']
	return ret

def get_vm_topo(vm_info, networks_info, topo, touch_ips, vm_port_netstats):
	# vm level
	vm = {
		'id': vm_info['id'],
		'status': vm_info['status'],
		'host': vm_info['OS-EXT-SRV-ATTR:host'],
		'name': vm_info['name'],
		'created_at': vm_info['created'],
		'addresses': {},
		'type': "virtual host",
		'check': {"result": None, "error_msg": ""},
		'next': []
	}

	for addr in vm_info["addresses"]:
		nets = vm_info["addresses"][addr]
		vm["addresses"][addr] = []
		for i in nets:
			a_addr = {
					"mac_addr": i['OS-EXT-IPS-MAC:mac_addr'],
					"version": i['version'],
					'addr': i['addr'],
					'cidr': None,
					'tag': None,
					'gateway_ip': None,
					'dhcp': None,
					'dhcp_netns': None,
					'type': i['OS-EXT-IPS:type'],
					'next': None,
					'check': {"result": None, "error_msg": ""},
					'performance': {"bandwidth": None, "delay": None, "error_msg": "", "evaluation": ""}
				}
			if vm_port_netstats == None:
				a_addr['performance']['bandwidth'] = get_vm_port_netstat_down()
			else:
				if a_addr['mac_addr'] in vm_port_netstats:
					a_addr['performance']['bandwidth'] = vm_port_netstats[a_addr['mac_addr']]
				else:
					a_addr['performance']['bandwidth'] = get_vm_port_netstat_down()
					if vm['status'] == 'ACTIVE':
						a_addr['check']['result'] = False
						a_addr['check']['error_msg'] = "vm interface lost(%s)." %(a_addr['mac_addr'])
						add_function_fault("vm:%s qemu-kvm interface lost(%s)." %(vm['id'], a_addr['mac_addr'])) 
			vm["addresses"][addr].append(a_addr)

	topo['device'].append(vm)

	vm_floating_ips = {}
	for net_name in vm['addresses']:
		for ip_addr in vm['addresses'][net_name]:
			if ip_addr['type'] != 'fixed':
				vm_floating_ips[ip_addr['addr']] = ip_addr

	for port in networks_info['ports']:
		port_addr = port['fixed_ips'][0]['ip_address']
		if port_addr in vm_floating_ips:
			port_net_info = get_port_network_info(port, networks_info)
			vm_floating_ips[port_addr]['gateway_ip'] = port_net_info['gateway_ip']
			vm_floating_ips[port_addr]['cidr'] = port_net_info['cidr']

	# tap level
	vm_fixed_ips = {}
	for net_name in vm["addresses"]:
		for ip_addr in vm["addresses"][net_name]:
			if ip_addr['type'] == 'fixed':
				touch_ips.add(ip_addr['addr'])
				vm_fixed_ips[ip_addr['addr']] = ip_addr
	
	tap_num = 0
	tap_index = len(topo['tap'])
	for port in networks_info["ports"]:
		port_addr = port['fixed_ips'][0]['ip_address']
		if port_addr in vm_fixed_ips:
			tap_info = {}
			tap_info['id'] = port['id']
			tap_info['name'] = "tap" + port['id'][:11]
			tap_info['mac_address'] = port['mac_address']
			tap_info['status'] = port['status']
			ret = get_tap_addr(port['fixed_ips'][0], networks_info)
			ret['type'] = 'fixed'
			tap_info['addresses'] = [ret]
			tap_info['netns'] = None
			tap_info['type'] = "tap device"
			tap_info['check'] = {"result": None, "error_msg": ""}
			tap_info['next'] = len(topo['qbr']) + tap_num
			topo['tap'].append(tap_info)
			vm['next'].append(len(topo['tap']) - 1)
			vm_fixed_ips[port_addr]['next'] = len(topo['tap']) - 1
			# ret_info = {
			# 'ip_address': port['fixed_ips'][0]['ip_address']
			# 'gateway_ip': None,
			# 'cidr': None,
			# 'dhcp': None
			# }
			port_net_info = get_port_network_info(port, networks_info)
			vm_fixed_ips[port_addr]['gateway_ip'] = port_net_info['gateway_ip']
			vm_fixed_ips[port_addr]['cidr'] = port_net_info['cidr']
			vm_fixed_ips[port_addr]['dhcp'] = port_net_info['dhcp']
			vm_fixed_ips[port_addr]['dhcp_netns'] = port_net_info['dhcp_netns']
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

def get_dhcp_name(port, networks_info):
	if port['name'] != '':
		return port['name']

	network_id = port['network_id']
	for net in networks_info['networks']:
		if net['id'] == network_id:
			return net['name'] + "-" + "dhcp"

def get_network_topo(networks_info, topo, touch_ips):
	# dhcp
	if not is_network_node():
		return

	for port in networks_info["ports"]:
		if port['device_owner'] == 'network:dhcp':
			dhcp_info = {}
			dhcp_info['id'] = port['id']
			dhcp_info['host'] = get_hostname()
			dhcp_info['name'] = get_dhcp_name(port, networks_info)
			dhcp_info['netns'] = "qdhcp-" + port['network_id']
			dhcp_info['created_at'] = port['created_at']
			dhcp_info['type'] = "dhcp"
			dhcp_info['status'] = port['status']
			dhcp_info['check'] = {"result": None, "error_msg": ""}
			dhcp_info['addresses'] = []
			addr = {
					"mac_addr": port['mac_address'],
					"version": 4,
					'addr': port['fixed_ips'][0]['ip_address'],
					'cidr': None,
					'tag': None,
					'gateway_ip': None,
					'dhcp': None,
					'dhcp_netns': None,
					'type': 'fixed',
					'next': None,
					'check': {"result": None, "error_msg": ""},
					'performance': {"bandwidth": None, "delay": None, "error_msg": "", "evaluation": ""}
			}
			dhcp_info['addresses'].append(addr)
			dhcp_info['next'] = len(topo['tap'])
			dhcp_info['addresses'][0]['next'] = len(topo['tap'])
			topo['device'].append(dhcp_info)

			tap_info = {}
			tap_info['id'] = port['id']
			tap_info['name'] = "tap" + port['id'][:11]
			tap_info['mac_address'] = port['mac_address']
			tap_info['status'] = port['status']
			tap_info['addresses'] = []
			for i in port['fixed_ips']:
				ret = get_tap_addr(i, networks_info)
				ret['type'] = 'fixed'
			 	tap_info['addresses'].append(ret)
			tap_info['type'] = "tap device"
			tap_info['netns'] = dhcp_info['netns']
			tap_info['check'] = {"result": None, "error_msg": ""}
			port_net_info = get_port_network_info(port, networks_info)
			dhcp_info['addresses'][0]['gateway_ip'] = port_net_info['gateway_ip']
			dhcp_info['addresses'][0]['cidr'] = port_net_info['cidr']
			dhcp_info['addresses'][0]['dhcp'] = port_net_info['dhcp']
			dhcp_info['addresses'][0]['dhcp_netns'] = port_net_info['dhcp_netns']
			#dhcp_info['addresses'][0]['next'] = 

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
		router_info['host'] = get_hostname()
		router_info['created_at'] = r['created_at']
		router_info['type'] = "router"
		router_info['netns'] = "qrouter-" + r['id']
		router_info['addresses'] = []
		router_info['status'] = r['status']
		router_info['check'] = {"result": None, "error_msg": ""}
		router_info['next'] = []
		topo['device'].append(router_info)
		# qr qg
		
		for port in networks_info['ports']:
			if port['device_id'] == router_info['id']:
				print router_info['next']
				#router_info['next'].append(len(topo['tap']))
				q_info = {}
				q_info['id'] = port['id']
				if port['device_owner'] == 'network:router_interface':
					q_info['name'] = "qr-" + port['id'][:11]
				else:
					q_info['name'] = "qg-" + port['id'][:11]
				q_info['mac_address'] = port['mac_address']
				q_info['status'] = port['status']
				q_info['netns'] = router_info['netns']
				q_info['addresses'] = []

			 	# 
			 	addr = {
					"mac_addr": q_info['mac_address'],
					"version": 4,
					'addr': port['fixed_ips'][0]['ip_address'],
					'cidr': None,
					'tag': None,
					'gateway_ip': None,
					'dhcp': None,
					'dhcp_netns': None,
					'type': 'fixed',
					'next': None,
					'check': {"result": None, "error_msg": ""},
					'performance': {"bandwidth": None, "delay": None, "error_msg": "", "evaluation": ""}
				}
				router_info['addresses'].append(addr)
				if port['device_owner'] != 'network:router_interface':
					# external network
					addr['type'] = 'floating'

				port_net_info = get_port_network_info(port, networks_info)
				addr['gateway_ip'] = port_net_info['gateway_ip']
				addr['cidr'] = port_net_info['cidr']
				addr['dhcp'] = port_net_info['dhcp']
				addr['dhcp_netns'] = port_net_info['dhcp_netns']
				addr['next'] = len(topo['tap'])
				ret = get_tap_addr(port['fixed_ips'][0], networks_info)
				ret['type'] = 'fixed'
				q_info['addresses'].append(ret)

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
					ret = get_tap_addr(port['fixed_ips'][0], networks_info)
					ret['type'] = 'floating'
					t['addresses'].append(ret)


def get_network_from_ip(ip):
	if ip == "":
		return "0.0.0.0/0"
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

def get_nic_ex_ip():
	# cidr
	ret, result = exe("ip address | grep br-ex")
	#if ret == False or len(result.split('\n')) < 1:
	if ret == False:
		add_function_fault("openvswitch bridge br-ex lost.")
		return ret, "openvswitch bridge br-ex lost."
	elif len(result.split('\n')) < 1:
		add_function_fault("external ip lost.")
		return ret, "external ip lost."
	ip = result.split('\n')[1].split()[1]
	return True, ip

def get_nic_ex_info(nic_ex_info):
	# nic_ex_info = {}
	# nic_ex_info['name'] = ""
	# nic_ex_info['device'] = ""
	# nic_ex_info['physical_device'] = ""
	# nic_ex_info['ip_address'] = ""
	# nic_ex_info['type'] = "ovs bridge"
	# nic_ex_info['check'] = {"result": None, "error_msg": ""}
	ret, result = get_nic_ex_ip()
	if ret == False:
		return ret, result
	nic_ex_info['ip_address'] = result
	
	ret, br_info = get_ovs_info(False)
	if ret == False:
		add_function_fault("openvswitch service down.")
		nic_ex_info['check']['result'] = False
		nic_ex_info['check']['error_msg'] = "openvswitch service down."
		return ret, br_info

	if 'br-ex' not in br_info:
		add_function_fault("openvswitch bridge br-ex lost.")
		nic_ex_info['check']['result'] = False
		nic_ex_info['check']['error_msg'] = "openvswitch bridge br-ex lost."

	for pd in br_info['br-ex']['Port']:
		if pd != "br-ex" and pd != "phy-br-ex":
			nic_ex_info['physical_device'] = pd
	nic_ex_info['device'] = 'br-ex'
	nic_ex_info['name'] = 'br-ex'
	return True, None

def get_nic_tun_ip():
	ret, result = exe('ovs-vsctl show | grep "local_ip"')
	if ret == False:
		if exe('ovs-vsctl show')[0] == False:
			add_function_fault("openvswitch service down.")
			return ret, "openvswitch service down."
		else:
			add_function_fault("openvswitch bridge br-tun lost.")
			return ret, "openvswitch bridge br-tun lost."

	start = result.find("local_ip")
	left = result.find("\"", start)
	right = result.find("\"", left + 1)
	tun_ip = result[left + 1: right]

	ret, result = exe('ip a | grep ' + tun_ip)
	if ret == False:
		add_function_fault("tunnel ip lost.")
		return ret, "tunnel ip lost."

	return True, result.strip().split(' ')[1]


def get_nic_tun_info(nic_tun_info):
	# nic_tun_info = {}
	tun_ip = nic_tun_info['ip_address']
	if tun_ip == "":
		return False, "tunnel ip lost."
	ret, result = exe('ip a | grep ' + tun_ip)
	if ret == False:
		nic_tun_info['check']['result'] = False
		add_function_fault("tunnel ip lost.")
		nic_tun_info['check']['error_msg'] = "tunnel ip lost."
		return ret, "tunnel ip lost."
	nic_tun_info['name'] = result.strip().split(' ')[-1]
	nic_tun_info['device'] = nic_tun_info['name']
	nic_tun_info['physical_device'] = nic_tun_info['name']
	return True, nic_tun_info

def get_tunnel_remote(br_tun):
	remote = []
	options = None
	for port in br_tun['Port']:
		if port.startswith("vxlan"):
			options = br_tun['Port'][port]['options']
	if options == None or len(options) < 2:
		return None
	options = options[1:-1]
	options = options.replace("\"", '')
	records = options.split(' ')
	for rec in records:
		if rec.startswith("remote_ip"):
			remote = rec.split('=')[1].split(',')		
	return remote

def get_extnet_gateway(ip_addr, networks_info):
	if ip_addr == "":
		return []
	net = get_network_from_ip(ip_addr)
	for sub in networks_info['subnets']:
		if sub['cidr'] == net:
			return [sub['gateway_ip']]
	return []

def check_service_status():
	# libvirt
	# openvswitch
	# other service
	all_node_service = ['libvirtd.service', 'openvswitch.service', 'rabbitmq-server.service']
	network_node_service = ['neutron-dhcp-agent.service', 'neutron-metadata-agent.service',
							'neutron-server.service', 'neutron-dhcp-agent.service', 
							'neutron-l3-agent.service',  'neutron-openvswitch-agent.service',
							'openstack-nova-api.service', 'openstack-nova-scheduler.service',
							'openstack-nova-compute.service', 'openstack-nova-conductor.service',
							 'openstack-nova-novncproxy.service', 'openstack-nova-consoleauth.service',
							 'mariadb.service']
	compute_node_service = ['openstack-nova-compute.service', 'neutron-openvswitch-agent.service']

	ret = {}
	for service in all_node_service:
		if check_service(service) == False:
			add_function_fault("%s service down." %(service))
			ret[service] = False
		else:
			ret[service] = True
	if is_network_node():
		for service in network_node_service:
			if check_service(service) == False:
				add_function_fault("%s service down." %(service))
				ret[service] = False
			else:
				ret[service] = True
	else:
		for service in compute_node_service:
			if check_service(service) == False:
				add_function_fault("%s service down." %(service))
				ret[service] = False
			else:
				ret[service] = True
	return True, ret

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

	vm_port_netstats = get_vm_port_netstats()
	if vm_port_netstats == None:
		AGENTLOG.error("agent.func.get_topo -  vm_port_netstats return none, libvirtd service down.")
		add_function_fault("libvirtd.service service down.")


	AGENTLOG.info("agent.func.get_topo -  get vm topo start.")
	for vm in vms_info:
		get_vm_topo(vm, networks_info, topo, touch_ips, vm_port_netstats)
	AGENTLOG.info("agent.func.get_topo -  get vm topo done.")


	AGENTLOG.info("agent.func.get_topo -  get network topo start.")
	if is_network_node():
		get_network_topo(networks_info, topo, touch_ips)
	AGENTLOG.info("agent.func.get_topo -  get network topo done.")

	AGENTLOG.info("agent.func.get_topo -  get ovs info start.")
	ret, br_info = get_ovs_info()
	if ret == False:
		br_info = None
		add_function_fault("openvswitch.service service down.")
		AGENTLOG.info("agent.func.get_topo -  openvswitch.service service down.")
	AGENTLOG.info("agent.func.get_topo -  get ovs info done.")

	br_int_info = {}
	br_int_info['name'] = 'br-int'
	br_int_info['type'] = "ovs bridge"
	br_int_info['check'] = {"result": None, "error_msg": ""}
	br_int_info['next'] = [0]
	if br_info != None and 'br-int' in br_info:
		br_int_info['info'] = br_info['br-int']
	else:
		br_int_info['info'] = None
		br_int_info['check']['result'] = False
		if br_info == None:
			br_int_info['check']['error_msg'] = "openvswitch.service service down."
		else:
			add_function_fault('openvswitch bridge br-int lost.')
			br_int_info['check']['error_msg'] = "openvswitch bridge br-int lost."
	
	topo['br-int'].append(br_int_info)

	br_tun_info = {}
	br_tun_info['name'] = 'br-tun'
	br_tun_info['info'] = None
	br_tun_info['type'] = "ovs bridge"
	br_tun_info['check'] = {"result": None, "error_msg": ""}
	br_tun_info['next'] = [0]
	if br_info != None and 'br-tun' in br_info:
		br_tun_info['info'] = br_info['br-tun']
	else:
		br_tun_info['check']['result'] = False
		if br_info == None:
			br_tun_info['check']['error_msg'] = "openvswitch.service service down."
		else:
			add_function_fault('openvswitch bridge br-tun lost.')
			br_tun_info['check']['error_msg'] = "openvswitch bridge br-tun lost."

	if br_info == None or 'br-tun' not in br_info:
		remote = []
	else:
		remote = get_tunnel_remote(br_tun_info['info'])
		if remote == None:
			br_tun_info['check']['result'] = False
			br_tun_info['check']['error_msg'] = "br-tun lost vxlan interface."
			add_function_fault("br-tun lost vxlan interface.")
	topo['ovs-provider'].append(br_tun_info)

	nic_tun_info = {}
	nic_tun_info['name'] = ""
	nic_tun_info['device'] = ""
	nic_tun_info['physical_device'] = ""
	# cidr
	nic_tun_info['ip_address'] = ""
	nic_tun_info['type'] = "nic"
	nic_tun_info['remote'] = remote
	nic_tun_info['performance'] = {"bandwidth": None, "delay": None, "error_msg": "", "evaluation": ""}
	nic_tun_info['check'] = {"result": None, "error_msg": ""}
	nic_tun_info['next'] = [0]

	AGENTLOG.info("agent.func.get_topo -  get_nic_tun_ip start.")
	ret, nic_tun_ip = get_nic_tun_ip()
	if ret == False:
		AGENTLOG.error("agent.func.get_topo -  get_nic_tun_ip return false, %s." %(nic_tun_ip))
		nic_tun_info['check']['result'] = False
		nic_tun_info['check']['error_msg'] = nic_tun_ip
	else:
		nic_tun_info['ip_address'] = nic_tun_ip
		#return ret, nic_tun_ip
	AGENTLOG.info("agent.func.get_topo -  get_nic_tun_ip done.")

	AGENTLOG.info("agent.func.get_topo -  get_nic_tun_info start.")
	ret, result = get_nic_tun_info(nic_tun_info)
	if ret == False:
		AGENTLOG.error("agent.func.get_topo -  get_nic_tun_info return false, %s." %(result))
	AGENTLOG.info("agent.func.get_topo -  get_nic_tun_info done.")

	nic_stats = get_nic_netstats()
	if nic_tun_info['name'] != "" and nic_tun_info['name'] in nic_stats:
		nic_tun_info['performance']['bandwidth'] = nic_stats[nic_tun_info['name']]
	else:
		if nic_tun_info['name'] not in nic_stats:
			nic_tun_info['performance']['error_msg'] = "can't get %s performance info." %(nic_tun_info['name'])
	topo['nic'].append(nic_tun_info)

	physical_switch_info = {}
	physical_switch_info['type'] = 'physical switch'
	# cidr
	physical_switch_info['network'] = get_network_from_ip(nic_tun_info['ip_address'])
	physical_switch_info['name'] = "physical switch " + physical_switch_info['network']
	physical_switch_info['check'] = {"result": None, "error_msg": ""}
	if physical_switch_info['network'] == '0.0.0.0/0':
		physical_switch_info['check']['result'] = False
		physical_switch_info['check']['error_msg'] = "nic of lost ip switch."
	physical_switch_info['next'] = None
	topo['physical-switch'].append(physical_switch_info)

	if is_network_node():
		# network node
		br_ex_info = {}
		br_ex_info['name'] = 'br-ex'
		br_ex_info['info'] = None
		br_ex_info['type'] = "ovs bridge"
		br_ex_info['check'] = {"result": None, "error_msg": ""}
		br_ex_info['next'] = [1]
		if br_info != None and 'br-ex' in br_info:
			br_ex_info['info'] = br_info['br-ex']
		else:
			br_ex_info['check']['result'] = False
			if br_info == None:
				br_ex_info['check']['error_msg'] = "openvswitch service down."
				add_function_fault('openvswitch service down.')
			else:		
				br_ex_info['check']['error_msg'] = "openvswitch bridge br-ex lost."
				add_function_fault('openvswitch bridge br-ex lost.')

		topo['ovs-provider'].append(br_ex_info)
		topo['br-int'][0]['next'].append(1)

		ret, nic_ex_ip = get_nic_ex_ip()
		if ret == False:
			AGENTLOG.error("agent.func.get_topo -  get_nic_ex_ip return false, %s." %(nic_ex_ip))
			#return ret, nic_ex_ip
		if nic_tun_ip == nic_ex_ip:
			# tunnel network and extnet network use same nic 
			br_ex_info['next'] = [0]
		else:
			nic_ex_info = {}
			nic_ex_info['name'] = ""
			nic_ex_info['device'] = ""
			nic_ex_info['physical_device'] = ""
			# cidr
			nic_ex_info['ip_address'] = ""
			nic_ex_info['type'] = "nic"
			nic_ex_info['check'] = {"result": None, "error_msg": ""}
			nic_ex_info['performance'] = {"bandwidth": None, "delay": None, "error_msg": "", "evaluation": ""}

			nic_ex_info['next'] = [1]
			AGENTLOG.info("agent.func.get_topo -  get_nic_ex_info start.")
			ret, error_msg = get_nic_ex_info(nic_ex_info)
			if ret == False:
				AGENTLOG.error("agent.func.get_topo -  get_nic_ex_info return error, %s." %(error_msg))

			if nic_ex_info['name'] != "" and nic_ex_info['name'] in nic_stats:
				nic_ex_info['performance']['bandwidth'] = nic_stats[nic_ex_info['name']]
			elif nic_ex_info['name'] not in nic_stats:
				nic_ex_info['performance']['error_msg'] = "can't get %s performance info." %(nic_ex_info['name'])
			nic_ex_info['remote'] = get_extnet_gateway(nic_ex_info['ip_address'], networks_info)
			if nic_ex_info['remote'] == [] and nic_ex_info['ip_address'] != "":
				nic_ex_info['check']['result'] = False
				nic_ex_info['check']['error_msg'] = "can't get external nic network gateway."
				add_function_fault("can't get external nic network gateway.")
			AGENTLOG.info("agent.func.get_topo -  get_nic_ex_info done.")
	
			physical_switch_info = {}
			physical_switch_info['type'] = 'physical switch'
			physical_switch_info['network'] = get_network_from_ip(nic_ex_info['ip_address'])
			physical_switch_info['name'] = "physical switch " + physical_switch_info['network']
			physical_switch_info['check'] = {"result": None, "error_msg": ""}
			if physical_switch_info['network'] == '0.0.0.0/0':
				physical_switch_info['check']['result'] = False
				physical_switch_info['check']['error_msg'] = "nic of lost ip switch."
			physical_switch_info['next'] = None
			topo['physical-switch'].append(physical_switch_info)

	return True, topo

def process_tap_info(info):
	tap_info = {}
	state = info.split("\n")[0].strip()
	state = state.split(" ")
	tap_info['name'] = state[1][:-1]
	tap_info['status'] = "active"
	#print (state[2][1:len(state[2]) - 1]).split(',')
	if "UP" not in ((state[2][1:len(state[2]) - 1]).split(',')):
		tap_info['status'] = "unactive"

	for i in range(len(state)):
		if state[i] == "state":
			if state[i + 1] != "UNKNOWN" and state[i + 1] != "UP":
				tap_info['status'] = "unactive"
				break
	tap_info['mac'] = info.split("\n")[1].strip().split(" ")[1]
	tap_info['inets'] = []
	inets = info.split("\n")[2:]
	for i in inets:
		info = i.strip().split(" ")
		if info[0] == 'inet':
			# cidr
			tap_info['inets'].append(info[1])
	return tap_info

def check_br_int_port(dev, topo):
	if dev['check']['result'] == False:
		return
	ret, ovs_info = get_ovs_info(False)
	if ret == False:
		dev['check']['result'] = False
		dev['check']['error_msg'] = "openvswitch service down."
		add_function_fault("openvswitch service down.")
	else:
		if 'br-int' not in ovs_info:
			dev['check']['result'] = False
			dev['check']['error_msg'] = "openvswitch not create bridge br-int."
			add_function_fault("openvswitch bridge br-int lost.")
			return

		ports = ovs_info['br-int']['Port']
		if dev['name'] not in ports:
			dev['check']['result'] = False
			dev['check']['error_msg'] = "openvswitch bridge br-int lost interface %s." %(dev['name'])
			add_function_fault("openvswitch bridge br-int lost interface %s." %(dev['name']))
		else:
			# check error
			if dev['type'] == "ovs internal" and ports[dev['name']]['type'] != "internal":
				dev['check']['result'] = False
				dev['check']['error_msg'] = "port-%s type-%s error." %(dev['name'], ports[dev['name']]['type'])
				add_function_fault("port-%s type-%s error." %(dev['name'], ports[dev['name']]['type']))
				return
			# check status
			# check flow rule
			dev['check']['result'] = True
			dev['tag'] = ports[dev['name']]['vlan']

def check_qvo(dev, topo):
	if dev['check']['result'] != False:
		if dev['type'] == "placeholder":
			dev['check']['result'] = True
		else:
			ret, info = exe("ip addr show %s" %(dev['name'].split('@')[0]))
			if ret == False:
				dev['check']['result'] = False
				dev['check']['error_msg'] = "dev: not exist." %(dev['name'])
			else:
				qvo_info = process_tap_info(info)
				if qvo_info['status'] == "unactive":
					dev['check']['result'] = False
					dev['check']['error_msg'] = "dev:%s down." %(dev['name'])
				else:
					dev['check']['result'] = True
	check_br_int_port(topo['br-int-port'][dev['next']], topo)

def check_qvb(dev, topo):
	if dev['check']['result'] != False:
		if dev['type'] == "placeholder":
			dev['check']['result'] = True	
		else:
			ret, info = exe("ip addr show %s" %(dev['name'].split('@')[0]))
			if ret == False:
				dev['check']['result'] = False
				dev['check']['error_msg'] = "dev: not exist." %(dev['name'])
			else:
				qvb_info = process_tap_info(info)
				if qvb_info['status'] == "unactive":
					dev['check']['result'] = False
					dev['check']['error_msg'] = "dev:%s down." %(dev['name'])
				else:
					dev['check']['result'] = True
	check_qvo(topo['qvo'][dev['next']], topo)

def get_bridge_info(br_name):
	br_info = {}
	ret, info = exe("brctl show %s" %(br_name))	
	if ret == False:
		add_function_fault("cmd:brctl show %s return error." %(br_name))
		return False, "cmd:brctl show %s return error." %(br_name)
	else:
		#if len(info.split('\n'))
		info = info.split('\n')[1:]
		records = info[0].split("\t")
		while '' in records:
			records.remove('')
		if len(records) < 4:
			add_function_fault('linux bridge %s lost.' %(br_name))
			return False, 'linux bridge %s lost.' %(br_name)
		else:
			br_info['name'] = records[0]
			br_info['id'] = records[1]
			br_info['STP'] = records[2]
			br_info['interfaces'] = []
			br_info['interfaces'].append(records[3])
			for i in range(len(info) - 1):
				interface = info[i + 1].strip().split("\t")
				if len(interface) > 1:
					add_function_fault('linux bridge %s info error format.' %(br_name))
					return False, 'linux bridge %s info error format.' %(br_name)
				else:
					br_info['interfaces'].append(interface[0])
		return True, br_info

def check_qbr(dev, topo):
	if dev['check']['result'] != False:
		if dev['type'] == "placeholder":
			dev['check']['result'] = True
		else:
			ret, br_info = get_bridge_info(dev['name'])
			if ret == False:
				dev['check']['result'] = False
				dev['check']['error_msg'] = br_info
			else:
				dev['check']['result'] = True
				for i in dev['interfaces']:
					if i not in br_info['interfaces']:
						dev['check']['result'] = False
						dev['check']['error_msg'] = "%s interface lost." %(i)
						add_function_fault("%s interface lost." %(i))
			# secure rules check

	check_qvb(topo['qvb'][dev['next']], topo)

def is_addr_match(tap_inets, dev_addrs):
	# tap_inets cide
	# dev_addrs {ip_address cidr}
	tap_inet_ips = set()
	for addr in tap_inets:
		tap_inet_ips.add(addr.split("/")[0])
	for addr in dev_addrs:
		if addr['ip_address'] not in tap_inet_ips:
			return False

	return True

def check_tap(dev, topo):
	if dev['check']['result'] != False:
		if dev['status'] != "ACTIVE":
			dev['check']['result'] = True
			dev['status'] = "unactive"
		else:
			ret = None
			info = None
			if "netns" in dev:
				ret, info = exe("ip netns exec %s ip addr show %s" %(dev['netns'], dev['name']))
			else:
				ret, info = exe("ip addr show %s" %(dev['name']))

			if ret == False:
				dev['check']['result'] = False
				dev['status'] = "unactive"
				dev['check']['error_msg'] = "tap %s not exist." %(dev['name'])
				add_function_fault("tap %s not exist." %(dev['name']))
			else:
				tap_info = process_tap_info(info)
				if tap_info['status'] != 'active':
					dev['check']['result'] = False
					dev['status'] = "unactive"
					dev['check']['error_msg'] = "tap:%s down." %(tap_info['name'])
					add_function_fault("tap:%s down." %(tap_info['name']))
				elif tap_info['mac'] != dev['mac_address']:
					dev['check']['result'] = False
					dev['status'] = "unactive"
					dev['check']['error_msg'] = "tap mac not match: %s - %s" %(tap_info['mac'], dev['mac_address'])
					add_function_fault("tap mac not match: %s - %s" %(tap_info['mac'], dev['mac_address']))
				elif is_addr_match(tap_info['inets'], dev['addresses']):
					dev['check']['result'] = False
					dev['status'] = "unactive"
					dev['check']['error_msg'] = "tap %s addr lost." %(dev['name'])
					add_function_fault("tap %s addr lost." %(dev['name']))
				else:
					dev['check']['result'] = True
					dev['status'] = "active"
	check_qbr(topo['qbr'][dev['next']], topo)


def check_vm(dev, topo):
	# id status host name created addresses type check performance next
	# vm state/network interface
	if dev['check']['result'] != False:
		ret, vm_info_in_host = get_vm_info_in_host()
		if ret == False:
			dev['check']['result'] = False
			dev['check']['error_msg'] = "libvirtd.service service down."
			add_function_fault("libvirtd.service service down.")
		elif dev['id'] not in vm_info_in_host:
			dev['check']['result'] = False
			dev['check']['error_msg'] = "vm %s hypervisor down." %(dev[name])
			add_function_fault("vm %s hypervisor down." %(dev[name]))
		else:
			vm_info = vm_info_in_host[dev['id']]
			net_info = {}
			if 'netstats' in vm_info:
				for net in vm_info['netstats']:
					net_info[net['mac']] = net

			if dev['status'] != 'ACTIVE':
				dev['check']['result'] = True
				dev['status'] = 'unactive'
			else:
				if vm_info['state'] != 'running':
					dev['status'] = 'unactive'
					dev['check']['result'] = False
					dev['check']['error_msg'] = "vm not running,state:%s" %(vm_info['state'])
					add_function_fault("vm %s not running, state %s" %(dev['name'], vm_info['state']))
				else:
					dev['status'] = 'active'
					dev['check']['result'] = True
					for addr in dev['addresses']:
						nets = dev['addresses'][addr]
						for i in nets:
							if i['type'] == 'fixed':
								if i['mac_addr'] in net_info:
									i['check']['result'] = True
									# add vm info
								else:
									i['check']['result'] = False
									i['check']['error_msg'] = "net interface lost."
									dev['check']['result'] = False
									dev['check']['error_msg'] = "net interface %s lost." %(i['mac_addr'])
									add_function_fault("net interface %s lost." %(i['mac_addr']))
	for i in range(len(dev['next'])):
		check_tap(topo['tap'][dev['next'][i]], topo)

def get_all_ns():
	ret, info = exe("ip netns show")
	if not ret:
		add_function_fault("cmd:'ip netns show' return error.")
		return False, "cmd:'ip netns show' return error."
	else:
		all_ns = set()
		info = info.split('\n')
		for i in info:
			all_ns.add(i.split(' ')[0])
		return True, all_ns
		
def check_ns_exist(ns):
	ret, all_ns = get_all_ns()
	if ret == False:
		return False
	if ns in all_ns:
		return True
	return False

def check_dhcp(dev, topo):
	if dev['check']['result'] != False:
		if dev['status'] != 'ACTIVE':
			dev['check']['result'] = True
			dev['status'] = 'status'
		else:
			if check_ns_exist(dev['netns']) == False:
				dev['check']['result'] = False
				dev['check']['error_msg'] = "netns-%s not exist." %(dev['netns'])
				add_function_fault("netns-%s not exist." %(dev['netns']))
				dev['status'] = "unactive"
			else:
				# pid dir and file
				ret, info = exe("ip netns exec %s ps -aux | grep dnsmasq | grep tap" %(dev['netns']))
				if ret == False:
					AGENTLOG.error("agent.func.check_dhcp -  cmd:ip netns exec %s ps -aux | grep dnsmasq \
						| grep tap return error." %(dev['netns']))
					dev['check']['result'] = False
					dev['check']['error_msg'] = "dnsmasq not running."
					add_function_fault("network-%s dhcp deamon process down." %(dev['netns'].split('-')[1]))
					dev['status'] = "unactive"
				else:
					# check other dncp info,such as configure
					dev['check']['result'] = True
					dev['check']['error_msg'] = ""
					dev['status'] = "active"
	
	check_tap(topo['tap'][dev['next']], topo)

def check_router(dev, topo):
	if dev['check']['result'] != False:
		if dev['status'] != "ACTIVE":
			dev['status'] = "unactive"
			dev['check']['result'] = True
		else:
			if check_ns_exist(dev['netns']) == False:
				dev['check']['result'] = False
				dev['check']['error_msg'] = "netns-%s not exist." %(dev['netns'])
				add_function_fault("router %s not exist." %(dev['name']))
				dev['status'] = "unactive"
			else:
				dev['check']['result'] = True
				dev['status'] = "active"

	# check route rules
	for i in dev['next']:
		check_tap(topo['tap'][i], topo)


def check_network_device(network_topo):
	AGENTLOG.info("agent.func.check_network_device -  1.check network device level start.")
	AGENTLOG.info("agent.func.check_network_device -  device num:%d." %(len(network_topo['device'])))

	for dev in network_topo['device']:
		AGENTLOG.info("agent.func.check_network_device - check device %s.%s ." %(dev['type'], dev['name']))
		if dev['type'] == 'virtual host':
			check_vm(dev, network_topo)
		elif dev['type'] == 'dhcp':
			check_dhcp(dev, network_topo)
		elif dev['type'] == 'router':
			check_router(dev, network_topo)
		else:
			AGENTLOG.error("agent.func.check_network_device -  unknown device type:%s." %(dev['type']))
			dev['result'] = False
			dev['error_msg'] = "unknown device type"
			add_function_fault("%s: unknown device type(%s)" %(dev['name'], dev['type']))
	AGENTLOG.info("agent.func.check_network_device -  1.check network device level done.")

def set_check(dev, result, msg = ""):
	dev['check']['result'] = result
	dev['check']['msg'] = msg


def check_network_ovs(network_topo):
	AGENTLOG.info("agent.func.check_network_ovs -  2.check network device nic start.")
	
	is_network = is_network_node()
	br_int = network_topo['br-int'][0]
	br_tun = network_topo['ovs-provider'][0]
	set_check(br_int, True)
	set_check(br_tun, True)
	br_ex = None
	if is_network:
		br_ex = network_topo['ovs-provider'][1]
		set_check(br_ex, True)

	status = check_service("openvswitch")
	if status == False:
		AGENTLOG.info("agent.func.check_network_ovs check_service openvswitch return error.")
		set_check(br_int, False, "openvswitch service down.")
		set_check(br_tun, False, "openvswitch service down.")
		if is_network:
			set_check(br_ex, False, "openvswitch service down.")
	else:
		if br_int['info'] != None:
			if ('patch-tun' not in br_int['info']['Port'] or br_int['info']['Port']['patch-tun']['options']
				!= "{peer=patch-int}" or br_int['info']['Port']['patch-tun']['type']!= 'patch'):
				set_check(br_int, False, "interface:patch-tun lost or config error.")
				add_function_fault("openvswitch bridge br-int lost interface:patch-tun or config error.")
		if br_tun['info'] != None:
			if ('patch-int' not in br_tun['info']['Port'] or br_tun['info']['Port']['patch-int']['type']
				!= "patch" or br_tun['info']['Port']['patch-int']['options'] != "{peer=patch-tun}"):
				set_check(br_tun, False, "interface:patch-int lost or config error.")
				add_function_fault("openvswitch bridge br-tun lost interface:patch-tun or config error.")

			vxlan_name = None
			for port in br_tun['info']['Port']:
				if port.startswith("vxlan"):
					vxlan_name = port

			if vxlan_name == None or br_tun['info']['Port'][vxlan_name]['type'] != 'vxlan':
				set_check(br_tun, False, "bridge br-tun lost vxlan interface.")
				add_function_fault("openvswitch bridge br-tun lost vxlan interface.")

		if is_network:
			if br_int['info'] != None:
				if ('int-br-ex' not in br_int['info']['Port'] or br_int['info']['Port']['int-br-ex']['options']
					!= "{peer=phy-br-ex}" or br_int['info']['Port']['int-br-ex']['type']!= 'patch'):
					set_check(br_int, False, "interface:int-br-ex lost or config error.")
					add_function_fault("openvswitch br_int lost int-br-ex interface.")
			if br_ex['info'] != None:
				if ('phy-br-ex' not in br_ex['info']['Port'] or br_ex['info']['Port']['phy-br-ex']['type'] !=
					"patch" or br_ex['info']['Port']['phy-br-ex']['options'] != "{peer=int-br-ex}"):
					set_check(br_ex, False, "interface:phy-br-ex lost or config error.")
					add_function_fault("openvswitch br_ex lost phy-br-ex interface.")

				ext_nic = None
				for port in br_ex['info']['Port']:
					if port != 'br-ex' and port != "phy-br-ex":
						ext_nic = port
				if ext_nic == None:
					set_check(br_ex, False, "external network nic interface lost.")
					add_function_fault("external network nic interface lost.")
				ret, info = exe("ip address show %s" %(ext_nic))
				if ret == False:
					set_check(br_ex, False, "external network nic %s not exist." %(ext_nic))
					add_function_fault("external network nic %s not exist.") %(ext_nic)

	# other check as flow
	AGENTLOG.info("agent.func.check_network_ovs -  2.check network device nic done.")

def get_nic_info(nic):
	nic_info = {'name': "", "status": "active", "master": "", "inets": [], "mac": None}
	ret, info = exe("ip address show %s" %(nic))
	if ret == False:
		AGENTLOG.error("agent.func.get_nic_info -  cmd:ip address show %s return error." %(nic))
		AGENTLOG.error("agent.func.get_nic_info -  %s not exist." %(nic))
		return None

	state = info.split("\n")[0].strip()
	state = state.split(" ")
	nic_info['name'] = state[1][:-1]
	nic_info['status'] = "active"
	#print (state[2][1:len(state[2]) - 1]).split(',')
	if "UP" not in ((state[2][1:len(state[2]) - 1]).split(',')):
		nic_info['status'] = "unactive"

	for i in range(len(state)):
		if state[i] == 'master':
			nic_info['master'] = state[i + 1]

	for i in range(len(state)):
		if state[i] == "state":
			if state[i + 1] != "UNKNOWN" and state[i + 1] != "UP":
				nic_info['status'] = "unactive"
				break
	nic_info['mac'] = info.split("\n")[1].strip().split(" ")[1]
	nic_info['inets'] = []
	inets = info.split("\n")[2:]
	for i in inets:
		info = i.strip().split(" ")
		if info[0] == 'inet':
			nic_info['inets'].append(info[1])

	return nic_info

def check_network_nic(network_topo):
	AGENTLOG.info("agent.func.check_network_nic -  3.check network device nic start.")
	is_network = is_network_node()
	nic_tun = network_topo['nic'][0]
	nic_ext = None
	if is_network and len(network_topo['nic']) == 2:
		nic_ext = network_topo['nic'][1]

	if nic_tun['check']['result'] != False:
		info = get_nic_info(nic_tun['name'])
		if info == None:
			set_check(nic_tun, False, "tunnel nic:%s lost." %(nic_tun['name']))
			add_function_fault("tunnel nic:%s lost." %(nic_tun['name']))
		elif info['status'] == "unactive":
			set_check(nic_tun, False, "tunnel nic:%s down." %(nic_tun['name']))
			add_function_fault("tunnel nic:%s down." %(nic_tun['name']))
		else:
			find_addr = False
			for inet in info['inets']:
				if inet == nic_tun['ip_address']:
					find_addr = True
			if find_addr == False:
				set_check(nic_tun, False, "tunnel nic:%s not has ip:%s" %(nic_tun['name'], nic_tun['ip_address']))
				add_function_fault("tunnel nic:%s not has ip:%s" %(nic_tun['name'], nic_tun['ip_address']))

	if nic_ext != None and nic_ext['check']['result'] != False:
		info = get_nic_info(nic_ext['device'])
		if info == None:
			set_check(nic_ext, False, "external nic:%s lost." %(nic_ext['name']))
			add_function_fault("external nic:%s lost." %(nic_ext['name']))
		elif info['status'] == 'unactive':
			set_check(nic_ext, False, "external nic:%s down." %(nic_ext['name']))
			add_function_fault("external nic:%s down." %(nic_ext['name']))
		else:
			find_addr = False
			for inet in info['inets']:
				if inet == nic_ext['ip_address']:
					find_addr = True
			if find_addr == False:
				set_check(nic_ext, False, "external nic:%s not has ip:%s" %(nic_ext['name'], nic_ext['ip_address']))
				add_function_fault("external nic:%s not has ip:%s" %(nic_ext['name'], nic_ext['ip_address']))

		info = get_nic_info(nic_ext['physical_device'])
		if info == None or info['status'] == 'unactive':
			set_check(nic_ext, False, "external physical nic:%s down." %(nic_ext['physical_device']))
			add_function_fault("external physical nic:%s down." %(nic_ext['physical_device']))
		elif info['master'] != 'ovs-system':
			set_check(nic_ext, False, "external physical nic:%s master error(%s)." %(nic_ext['physical_device'],
				info['master']))
			add_function_fault("external physical nic:%s master error(%s)." %(nic_ext['physical_device'],
				info['master']))

	AGENTLOG.info("agent.func.check_network_nic -  3.check network device nic done.")


def check_network_config(network_topo):
	AGENTLOG.info("agent.func.check_network_config -  check network start.")
	# 1."device" 2."tap" 3."qbr" 4."qvb" 5."qvo" 6."br-int-port" 
	# 7."br-int" 8."ovs-provider" 9."nic" 10."physical-switch"
	check_network_device(network_topo)
	check_network_ovs(network_topo)
	check_network_nic(network_topo)
	AGENTLOG.info("agent.func.check_network_config -  check network done.")

def get_test_ip(ip, mask):
	mask = int(mask)
	last_mask = 32 - mask
	ip_split = ip.split('.')
	for i in range(len(ip_split)):
		ip_split[i] = int(ip_split[i])
	i = len(ip_split)
	while last_mask >= 8:
		i -= 1
		last_mask -= 8
		ip_split[i] = 255

	if last_mask > 0:
		ip_split[i] = ip_split[i] / pow(2, last_mask) + pow(2, last_mask)
	ip_split[len(ip_split) - 1] -= 1

	test_ip = ""
	for i in range(len(ip_split)):
		if i != 0:
			test_ip += "."
		test_ip += str(ip_split[i])
	test_ip += "/" + str(mask)
	return test_ip

def create_netns(netns):
	if check_ns_exist(netns):
		AGENTLOG.info("agent.func.is_connect -  netns:%s exist." %(netns))
		return True
	else:
		AGENTLOG.info("agent.func.is_connect -  create netns:%s." %(netns))
		ret, info = exe("ip netns add %s" %(netns))
		if ret == False:
			AGENTLOG.error("agent.func.is_connect -  cmd:ip netns add %s return error." %(netns))
			return False
		else:
			return True

def create_ovs_port(bridge, port, tag):
	ret, info = get_ovs_info(False)
	if ret == False:
		AGENTLOG.error("agent.func.create_ovs_port -  get ovs info error.")
		return ret
	if bridge not in info:
		AGENTLOG.error("agent.func.create_ovs_port -  bridge:%s not exist." %(bridge))
		return False
	if port in info[bridge]['Port']:
		AGENTLOG.error("agent.func.create_ovs_port -  port:%s exist in bridge%s." %(port, bridge))
		return False

	ret, info = exe("ovs-vsctl add-port %s %s tag=%s -- set Interface %s type=internal"
					%(bridge, port, tag, port))
	if ret == False:
		AGENTLOG.error("agent.func.create_ovs_port -  %s." %(info))
		return False
	return True

def set_tap_to_netns(port, netns):
	ret, info = exe("ip link set %s netns %s" %(port, netns))
	if ret == False:
		AGENTLOG.error("agent.func.set_tap_to_netns -  %s." %(info))
		return False
	return True

def bond_tap_addr(port, netns, addr):
	# addr cidr
	if netns == "":
		ret, info = exe("ip addr add %s dev %s" %(addr, port))
	else:
		ret, info = exe("ip netns exec %s ip addr add %s dev %s" %(netns, addr, port))
	if ret == False:
		AGENTLOG.error("agent.func.bond_tap_addr -  %s." %(info))
		return ret

	if netns == "":
		ret, info = exe("ifconfig %s promisc up" %(port))
	else:
		ret, info = exe("ip netns exec %s ifconfig %s promisc up" %(netns, port))
	if ret == False:
		AGENTLOG.error("agent.func.bond_tap_addr -  %s." %(info))
		return ret

	return True

def ping_test(ip, netns):
	if netns == "":
		ret, info = exe("ping %s -i 0 -c 3 -W 1 -q" %(ip))
	else:
		ret, info = exe("ip netns exec %s ping %s -i 0 -c 3 -W 1 -q" %(netns, ip))

	if ret == False:
		AGENTLOG.error("agent.func.ping_test -  %s." %(info))
		return False, info

	statistic = info.split("\n")[3]
	receive_count = int(statistic.split(",")[1].strip().split(' ')[0])

	if receive_count >= 1:
		return True, None
	else:
		return False, "all packets lost."

def clear_netns_and_port(netns, port):
	exe("ip netns del %s" %(netns))
	exe("ovs-vsctl del-port %s %s" %("br-int", port))

def is_connect_internal(vm_id, ip, mask, tag):
	# print mask
	test_ip = get_test_ip(ip, mask)
	format_ip = "-".join(ip.split('.'))
	netns = "%s_%s" %(vm_id[:11], format_ip)
	# ip netns add ns1
	# ovs-vsctl add-port br-int tap0 tag=1 -- set Interface tap0 type=internal
	# ip a
	# ovs-vsctl show
	# ip link set tap0  netns ns1
	# ip netns exec ns1 ip addr add 192.168.1.3/24 dev tap0
	# ip netns exec ns1 ifconfig tap0 promisc up
	# ip netns exec ns1 ip a
	# ip netns exec ns1 ping 192.168.1.1
	bridge = "br-int"
	port = "vm-%s" %(vm_id[:11])
	ret = create_netns(netns)
	if ret == False:
		clear_netns_and_port(netns, port)
		return False, "create netns error."

	ret = create_ovs_port(bridge, port, tag)
	if ret == False:
		clear_netns_and_port(netns, port)
		return False, "create ovs port error."

	ret = set_tap_to_netns(port, netns)
	if ret == False:
		clear_netns_and_port(netns, port)
		return False, "set tap to netns error."

	ret = bond_tap_addr(port, netns, test_ip)
	if ret == False:
		clear_netns_and_port(netns, port)
		return False, "bond tap addr error."

	ret, msg = ping_test(ip, netns)
	if ret == False:
		clear_netns_and_port(netns, port)
		return ret, "can't reach %s by ping, %s." %(ip, msg)

	#clear
	clear_netns_and_port(netns, port)
	return True, None

def is_connect_external(ip, mask, tag = None):
	netns = None
	ret, msg = ping_test(ip, netns)
	if ret == False:
		return ret, "can't reach %s by ping, %s." %(ip, msg)
	return True, None

def get_device_vm_tag(dev, topo):
	for net in dev['addresses']:
		for addr in dev['addresses'][net]:
			if addr['type'] == 'fixed':
				next_ = topo['tap'][addr['next']]['next']
				next_ = topo['qbr'][next_]['next']
				next_ = topo['qvb'][next_]['next']
				next_ = topo['qvo'][next_]['next']
				tag = topo['br-int-port'][next_]['tag']
				addr['tag'] = tag

def get_device_other_tag(dev, topo):
	for addr in dev['addresses']:
		if addr['type'] == 'fixed':
			next_ = topo['tap'][addr['next']]['next']
			next_ = topo['qbr'][next_]['next']
			next_ = topo['qvb'][next_]['next']
			next_ = topo['qvo'][next_]['next']
			tag = topo['br-int-port'][next_]['tag']
			addr['tag'] = tag

def check_device_connection(dev, topo):
	dest_list = []
	if dev['type'] == "virtual host" and dev['check']['result'] == True:
		get_device_vm_tag(dev, topo)
		#vm
		# for every addr
		# ip net tag
		for net in dev['addresses']:
			for addr in dev['addresses'][net]:
				if addr['type'] == 'fixed':
					ip = addr['addr']
					tag = addr['tag']
					mask = addr['cidr'].split('/')[1]
					dest_list.append({"id": dev['id'], "ip": ip, "mask": mask, "tag": tag, 'addr': addr})
	elif (dev['type'] == "dhcp" or dev['type'] == 'router') and dev['check']['result'] == True:
		get_device_other_tag(dev, topo)
		for addr in dev['addresses']:
			if addr['type'] == 'fixed':
				ip = addr['addr']
				tag = addr['tag']
				mask = addr['cidr'].split('/')[1]
				dest_list.append({"id": dev['id'], "ip": ip, "mask": mask, "tag": tag, 'addr': addr})
	else:
		AGENTLOG.error("agent.func.check_device_connection -  unknown device type:%s." %(dev['type']))
		set_check(dev, False, "unknown device type:%s." %(dev['type']))
		add_function_fault("%s has unknown device type:%s." %(dev['name'], dev['type']))
	
	for dst in dest_list:
			ret, error_info = is_connect_internal(dst['id'], dst['ip'], dst['mask'], dst['tag'])
			if ret == False:
				set_check(dst['addr'], False, "dev:%s addr:%s can't reach openvswitch, %s." 
					%(dev['name'], dst['addr']['addr'], error_info))
				set_check(dev, False, "addr:%s can't reach openvswitch, %s." 
					%(dst['addr']['addr'], error_info))
				add_function_fault("dev:%s addr:%s can't reach openvswitch, %s." 
					%(dev['name'], dst['addr']['addr'], error_info))
			else:
				set_check(dst['addr'], True)

def check_nic_connection(dev, topo):
	if dev['check']['result'] != False:
		set_check(dev, True)
		for ip in dev['remote']:
			ret, info = ping_test(ip, "")
			if ret == False:
				set_check(dev, False, "can't reach %s, %s" %(ip, info))
				add_function_fault("dev:%s cant't reach %s, %s" %(dev['name'], ip, info))
				return                                    

def check_network_connection(topo):
	AGENTLOG.info("agent.func.check_network_connection -  check network connection start.")
	for dev in topo['device']:
		AGENTLOG.info("agent.func.check_network_connection - check device  %s.%s connection." 
			%(dev['type'], dev['name']))
		check_device_connection(dev, topo)

	for dev in topo['nic']:
		AGENTLOG.info("agent.func.check_network_connection - check nic  %s.%s connection." 
			%(dev['type'], dev['name']))
		check_nic_connection(dev, topo)

	AGENTLOG.info("agent.func.check_network_connection -  check network connection done.")


if __name__ == '__main__':
	# print get_vm_uuids()
	# print get_host_ip()
	# print is_network_node()
	# print check_service("openstack-nova-compute")
	# print is_network_node()

	#print get_topo(valid_vm_info, networks_info)
	pass
	    