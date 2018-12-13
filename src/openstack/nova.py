#!/usr/bin/python2
from novaclient import client as nvclient
from keystoneauth1.identity import v3
from keystoneauth1 import session
from keystoneclient.v3 import client
from keystoneclient.v3 import tokens
auth = v3.Password(auth_url='http://192.168.122.9:5000/v3',
                   username='admin',
                   password='e60ed34c828d44b9',
                   project_name='admin',
                   project_domain_name='Default',
                   user_domain_name='Default')
sess = session.Session(auth=auth)
auth_token = sess.get_token()
print auth_token
kw = {}
kw['project_domain_id'] = 'default'
nova = nvclient.Client("2", auth_token=auth_token, auth_url='http://192.168.122.9:5000/v3',project_name='admin', **kw)
print nova.servers.list()
s = nova.servers.list()
print s[0].__dict__
print s[0]._info
print s[0].to_dict()
