#!/usr/bin/python2
from novaclient import client as nvclient
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client
from keystoneclient.v3 import tokens
from auth import get_token


def get_project_server_info(auth_token, auth_url, project_name):
    kw = {}
    kw['project_domain_id'] = 'default'
    nova = nvclient.Client("2", auth_token = auth_token, auth_url = auth_url, project_name = project_name, **kw)
    # print nova.servers.list()
    s = nova.servers.list()
    h = nova.hypervisors.list()
    print h[0].to_dict()
    #print h[0].__dict__
    # print s[0].__dict__
    # print s[0]._info
    print len(s)
    print s[0].to_dict()

if __name__ == '__main__':
	auth_url = 'http://192.168.122.9:5000/v3'
	username = 'test'
	password = '111111'
	project_name = 'test'
	auth_token = get_token(username, password, auth_url, project_name)
	if auth_token == None:
		print 'auth fail.'
		exit(0)
	get_project_server_info(auth_token, auth_url, project_name)

