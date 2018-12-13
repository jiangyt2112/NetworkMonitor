#!/usr/bin/python2
from neutronclient.v2_0 import client
from auth import get_token

def get_project_network_info(auth_token, auth_url):
	neutron = client.Client(auth_url = auth_url, token = auth_token)
    print neutron.list_networks()
    print neutron.list_subnets()
    print neutron.list_ports()

if __name__ == '__main__':
	auth_url = 'http://192.168.122.9:5000/v3'
	username = 'test'
	password = '111111'
	project_name = 'test'
	auth_token = get_token(username, password, auth_url, project_name)
	if auth_token == None:
		print 'auth fail.'
		exit(0)
	get_project_network_info(auth_token, auth_url)
