import libvirt
import libxml2
import json


odic = {}
conn = libvirt.openReadOnly(None)
if conn is None:
    odic['alldomains'] = ''
    odic['error'] = 'Failed to open connection to the hypervisor'
else:
    doms = conn.listAllDomains()
    # print doms
    domainlist=[]
    for dom in doms:
        ddic = {}
        ddic['uuid'] = dom.UUIDString()
        
    odic['alldomains'] = domainlist
    odic['error'] = ''
