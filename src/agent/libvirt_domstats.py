#!/usr/bin/env python
#encoding: utf-8

# ref:
# https://github.com/libvirt/libvirt-python/blob/master/examples/dominfo.py
# https://libvirt.org/docs/libvirt-appdev-guide-python/en-US/html/libvirt_application_development_guide_using_python-Guest_Domains-Monitoring.html

import libvirt
import libxml2
import json

def get_val_by_path(ctx, path):
    res = ctx.xpathEval(path)
    if res is None or len(res) == 0:
        value = "Unknown"
    else:
        value = res[0].content
    return value

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
        state, maxmem, usedmem, vcpus, cputime  = dom.info()
        ddic['uuid'] = dom.UUIDString()
        if state == 0:
            ddic['state'] = 'nostate'
        elif state == 1:
            ddic['state'] = 'running'
        elif state == 2:
            ddic['state'] = 'blocked'
        elif state == 3:
            ddic['state'] = 'paused'
        elif state == 4:
            ddic['state'] = 'shutdown'
        elif state == 5:
            ddic['state'] = 'shutoff'
        elif state == 6:
            ddic['state'] = 'crashed'
        elif state == 7:
            ddic['state'] = 'pmsuspended'

        ddic['maxmem'] = str(maxmem)
        ddic['usedmem'] = str(usedmem)
        ddic['vcpus'] = str(vcpus)
        ddic['cputime'] = str(cputime / 1000000000)

        if ddic['state'] == 'running':
            xmldesc = dom.XMLDesc(0)
            doc = libxml2.parseDoc(xmldesc)
            ctx = doc.xpathNewContext()

            cpudic = {}
            cpustats = dom.getCPUStats(True)[0]
            for name in cpustats:
                cpudic[name] = str(cpustats[name] / 1000000000)
            ddic['cpustats'] = cpudic

            memdic = {}
            memstats  = dom.memoryStats()
	    #print memstats
            for name in memstats:
                memdic[name] = str(memstats[name])
            ddic['memstats'] = memdic

            devs = ctx.xpathEval("/domain/devices/*")
            disklist = []
            netlist = []
            for d in devs:
                ctx.setContextNode(d)
                devcata = d.get_name()
                dev = get_val_by_path(ctx, "target/@dev")
                if devcata == 'disk':
                    rd_req, rd_bytes, wr_req, wr_bytes, err = dom.blockStats(dev)
                    adic = {}
                    type1 = get_val_by_path(ctx, "@type")
                    if type1 == "file":
                        adic['source'] = get_val_by_path(ctx, "source/@file")
                    elif type1 == "block":
                        adic['source'] = get_val_by_path(ctx, "source/@dev")
                    adic['target'] = get_val_by_path(ctx, "target/@dev")
                    adic['rd_req'] = str(rd_req)
                    adic['rd_bytes'] = str(rd_bytes)
                    adic['wr_req'] = str(wr_req)
                    adic['wr_bytes'] = str(wr_bytes)
                    adic['err'] = str(err)
                    disklist.append(adic)
                elif devcata == 'interface':
                    stats = dom.interfaceStats(dev)
                    adic = {}
                    adic['source'] = get_val_by_path(ctx, "source/@bridge")
                    adic['mac'] = get_val_by_path(ctx, "mac/@address")
                    adic['rd_bytes'] = str(stats[0])
                    adic['rd_pkts'] = str(stats[1])
                    adic['rd_err'] = str(stats[2])
                    adic['rd_drop'] = str(stats[3])
                    adic['wr_bytes'] = str(stats[4])
                    adic['wr_pkts'] = str(stats[5])
                    adic['wr_err'] = str(stats[6])
                    adic['wr_drop'] = str(stats[7])
                    netlist.append(adic)
            ddic['diskstats'] = disklist
            ddic['netstats'] = netlist
        domainlist.append(ddic)
    odic['alldomains'] = domainlist
    odic['error'] = ''

for i in odic['alldomains']:
    print i
    print ""
#out = json.dumps(odic)
#print out

