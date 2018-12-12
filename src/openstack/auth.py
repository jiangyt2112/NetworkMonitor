#!/usr/bin/python2
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client
from keystoneclient.v3 import tokens
auth = v3.Password(auth_url='http://192.168.122.9:5000/v3',
                   username='test',
                   password='111111',
                   project_name='test',
                   project_domain_name='Default',
                   user_domain_name='Default')
sess = session.Session(auth=auth)
auth_token = sess.get_token()
print auth_token

auth = v3.Token(auth_url='http://192.168.122.9:5000/v3', token = auth_token,project_domain_name='Default',project_name='test')
sess = session.Session(auth=auth)

keystone = client.Client(token = auth_token, auth_url = 'http://192.168.122.9:5000/v3', session = sess, endpoint = 'http://192.168.122.9:5000/v3')

print keystone.authenticate()
print keystone.users.list()
print keystone.projects.list()
