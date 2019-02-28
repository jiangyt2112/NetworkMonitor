#!/usr/bin/python2
import __init__
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client
from keystoneclient.v3 import tokens

def get_token(username, password, auth_url, project_name):
	auth = v3.Password(auth_url= auth_url,
		               username=username,
		               password=password,
		               project_name=project_name,
		               project_domain_name='Default',
		               user_domain_name='Default')
	sess = session.Session(auth=auth)
	try:
		auth_token = sess.get_token()
	except Exception, e:
		return None
	return auth_token


#auth = v3.Token(auth_url='http://192.168.122.9:5000/v3', token = auth_token,project_domain_name='Default',project_name='test')
#sess = session.Session(auth=auth)

#keystone = client.Client(token = auth_token, auth_url = 'http://192.168.122.9:5000/v3', session = sess, endpoint = 'http://192.168.122.9:5000/v3')

#print keystone.authenticate()
#print keystone.users.list()
#print keystone.projects.list()

def check_auth(auth_url, token, project_name):
	keystone = client.Client(token = auth_token, auth_url = auth_url)#, endpoint = auth_url)
	return keystone.authenticate()

if __name__ == "__main__":
	auth_url = 'http://192.168.122.9:5000/v3'
	username = 'admin'
	password = 'e60ed34c828d44b9'
	project_name = 'admin'
	auth_token = get_token(username, password, auth_url, project_name)
	print auth_token
	print check_auth(auth_url, auth_token, project_name)
