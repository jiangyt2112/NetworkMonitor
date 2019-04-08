#!/usr/bin/python2
from neutronclient.v2_0 import client
from auth import get_token

def get_project_network_info(auth_token, auth_url, endpoint):
	neutron = client.Client(auth_url = auth_url, token = auth_token, endpoint_url = endpoint)
	#print neutron.list_networks()
	#print neutron.list_subnets()
	#print neutron.list_ports()
	network_info = {"networks": [], "subnets": [], "ports": [], "routers": None}
	network_attributes = ['provider:physical_network', 'port_security_enabled', 'provider:network_type', 'id',
						'router:external', 'availability_zones', 'shared', 'project_id', 'status', 'subnets',
						'updated_at', 'provider:segmentation_id', 'name', 'admin_state_up', 'tenant_id', 'created_at',
						'mtu']
	subnet_attributes = ['host_routes', 'enable_dhcp', 'network_id', 'tenant_id', 'created_at', 'updated_at',
						'allocation_pools', 'gateway_ip', 'ip_version', 'cidr', 'project_id', 'id', 'name']
	port_attributes = ['updated_at', 'device_owner', 'port_security_enabled', 'fixed_ips', 'id',  
					'binding:vif_details', 'binding:vif_type', 'mac_address', 'project_id', 'status', 'binding:host_id', 
					'device_id', 'name', 'admin_state_up', 'network_id', 'tenant_id', 'created_at', 'binding:vnic_type']
	networks = (neutron.list_networks())["networks"]
	subnets = (neutron.list_subnets())["subnets"]
	ports = (neutron.list_ports())["ports"]
	routers = (neutron.list_routers())["routers"]
	
	for network in networks:
		info = {}
		for key in network_attributes:
			info[key] = network[key]
		network_info["networks"].append(info)

	for subnet in subnets:
		info = {}
		for key in subnet_attributes:
			info[key] = subnet[key]
		network_info["subnets"].append(info)

	for port in ports:
		info = {}
		for key in port_attributes:
			info[key] = port[key]
		network_info["ports"].append(info)

	network_info["routers"] = routers
	return network_info

if __name__ == '__main__':
	auth_url = 'http://192.168.122.2:5000/v3'
	endpoint_url = 'http://192.168.122.2:9696'
	username = 'admin'
	password = '1787f5020b4d451e'
	project_name = 'admin'
	auth_token = get_token(username, password, auth_url, project_name)
	if auth_token == None:
		print 'auth fail.'
		exit(0)
	get_project_network_info(auth_token, auth_url, endpoint_url)
