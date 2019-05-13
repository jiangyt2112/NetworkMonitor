#!/usr/bin/python2
import __init__
import libvirt
import libxml2
import json
import time
import psutil

def get_val_by_path(ctx, path):
    res = ctx.xpathEval(path)
    if res is None or len(res) == 0:
        value = "Unknown"
    else:
        value = res[0].content
    return value


{
    'uuid': '61205745-b2bf-4db0-ad50-e7a60bf08bd5', 
    'cpustats': {'cpu_time': '65230', 'system_time': '18214', 'user_time': '23891'}, 
    'state': 'running', 
    'cputime': '65230', 
    'usedmem': '524288', 
    'vcpus': '1', 
    'diskstats': [{'wr_req': '215', 'target': 'vda', 'err': '-1', 'rd_req': '1229', 'source': '/var/lib/nova/instances/61205745-b2bf-4db0-ad50-e7a60bf08bd5/disk', 'rd_bytes': '20610048', 'wr_bytes': '576512'}], 
    'memstats': {'last_update': '0', 'actual': '524288', 'rss': '153580'}, 
    'netstats': [
        {
            'wr_pkts': '180', 
            'rd_drop': '0', 
            'rd_pkts': '183', 
            'rd_err': '0', 
            'rd_bytes': '21767', 
            'wr_err': '0', 
            'source': 'qbr3ef787ad-67', 
            'mac': 'fa:16:3e:5d:9e:22', 
            'wr_drop': '0', 
            'wr_bytes': '20728'}], 
    'maxmem': '524288'
}

def get_vm_info_in_host():
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

    vm_info = {}
    if odic['alldomains'] == '':
        return False, "Failed to open connection to the hypervisor"
    else:
        for vm in odic['alldomains']:
            vm_info[vm['uuid']] = vm
    return True, vm_info


def get_vm_cpu_info():
    cpu_info = {}
    conn = libvirt.openReadOnly(None)
    if conn is None:
        return cpu_info
    else:
        doms = conn.listAllDomains()

        for dom in doms:
            state, maxmem, usedmem, vcpus, cputime  = dom.info()
            uuid = dom.UUIDString()
            state_str = ""
            if state == 0:
                state_str = 'nostate'
            elif state == 1:
                state_str = 'running'
            elif state == 2:
                state_str = 'blocked'
            elif state == 3:
                state_str = 'paused'
            elif state == 4:
                state_str = 'shutdown'
            elif state == 5:
                state_str = 'shutoff'
            elif state == 6:
                state_str = 'crashed'
            elif state == 7:
                state_str = 'pmsuspended'

            if state_str == 'running':    
                cpustats = dom.getCPUStats(True)[0]
                cpudic = {}
                cpu_info[uuid] = cputime
            else:
                cpu_info[uuid] = 0
    return cpu_info


def get_vm_port_netinfo():
    netinfo = {}
    conn = libvirt.openReadOnly(None)
    if conn is None:
        return netinfo
    else:

        doms = conn.listAllDomains()
        for dom in doms:
            state, maxmem, usedmem, vcpus, cputime  = dom.info()
            state_str = ""
            if state == 0:
                state_str = 'nostate'
            elif state == 1:
                state_str = 'running'
            elif state == 2:
                state_str = 'blocked'
            elif state == 3:
                state_str = 'paused'
            elif state == 4:
                state_str = 'shutdown'
            elif state == 5:
                state_str = 'shutoff'
            elif state == 6:
                state_str = 'crashed'
            elif state == 7:
                state_str = 'pmsuspended'

            if state_str == 'running':
                xmldesc = dom.XMLDesc(0)
                doc = libxml2.parseDoc(xmldesc)
                ctx = doc.xpathNewContext()
                devs = ctx.xpathEval("/domain/devices/*")
                
                for d in devs:
                    ctx.setContextNode(d)
                    devcata = d.get_name()
                    dev = get_val_by_path(ctx, "target/@dev")
                    if devcata == 'interface':
                        stats = dom.interfaceStats(dev)
                        
                        mac = get_val_by_path(ctx, "mac/@address")
                        netinfo[mac] = {}
                        netinfo[mac]['rd_bytes'] = int(stats[0])
                        netinfo[mac]['rd_pkts'] = int(stats[1])
                        netinfo[mac]['rd_err'] = int(stats[2])
                        netinfo[mac]['rd_drop'] = int(stats[3])

                        netinfo[mac]['wr_bytes'] = int(stats[4])
                        netinfo[mac]['wr_pkts'] = int(stats[5])
                        netinfo[mac]['wr_err'] = int(stats[6])
                        netinfo[mac]['wr_drop'] = int(stats[7])
    return netinfo


def get_vm_port_netstats():
    old_netinfo = get_vm_port_netinfo()
    time.sleep(1)
    new_netinfo = get_vm_port_netinfo()

    if old_netinfo == None or new_netinfo == None:
        return None
    netstats = {}
    for mac in old_netinfo:
        netstats[mac] = {
            "rx": {"packets": new_netinfo[mac]['rd_pkts'] - old_netinfo[mac]['rd_pkts'], 
                    "bytes": new_netinfo[mac]['rd_bytes'] - old_netinfo[mac]['rd_bytes'], 
                    "drop": new_netinfo[mac]['rd_drop'] - old_netinfo[mac]['rd_drop'],
                    "err": new_netinfo[mac]['rd_err'] - old_netinfo[mac]['rd_err']
                    },
            "tx": {"packets": new_netinfo[mac]['wr_pkts'] - old_netinfo[mac]['wr_pkts'], 
                    "bytes": new_netinfo[mac]['wr_bytes'] - old_netinfo[mac]['wr_bytes'], 
                    "drop": new_netinfo[mac]['wr_drop'] - old_netinfo[mac]['wr_drop'],
                    "err": new_netinfo[mac]['wr_err'] - old_netinfo[mac]['wr_err']
                    }
                }
    return netstats
    
def get_vm_port_netstat_down():
    return {
        "rx": {"packets": 0, "bytes": 0, "drop": 0, "err": 0},
        "tx": {"packets": 0, "bytes": 0, "drop": 0, "err": 0}
    }

def get_nic_netinfo():
    nics_info = psutil.net_io_counters(pernic=True)
    nics_name = nics_info.keys()
    # keys = ["bytes_sent", "bytes_recv", "packets_sent", "packets_recv", "dropin", "dropout"]
    ret = {}
    for nic in nics_name:
        nic_info = nics_info[nic]
        ret[nic] = {
            "rx": {"packets": nic_info.packets_recv, 
                    "bytes": nic_info.bytes_recv, 
                    "drop": nic_info.dropin,
                    "err": nic_info.errin
                    },
            "tx": {"packets": nic_info.packets_sent, 
                    "bytes": nic_info.bytes_sent, 
                    "drop": nic_info.dropout,
                    "err": nic_info.errout
                    }
            }
    return ret

def get_nic_netstats():
    old_info = get_nic_netinfo()
    time.sleep(1)
    new_info = get_nic_netinfo()

    nics_name = psutil.net_io_counters(pernic=True).keys()
    ret = {}
    for nic in nics_name:
        ret[nic] = {
            "rx": {"packets": new_info[nic]["rx"]['packets'] - old_info[nic]["rx"]['packets'], 
                    "bytes": new_info[nic]["rx"]['bytes'] - old_info[nic]["rx"]['bytes'], 
                    "drop": new_info[nic]["rx"]['drop'] - old_info[nic]["rx"]['drop'],
                    "err": new_info[nic]["rx"]['err'] - old_info[nic]["rx"]['err']
                    },
            "tx": {"packets": new_info[nic]["tx"]['packets'] - old_info[nic]["tx"]['packets'], 
                    "bytes": new_info[nic]["tx"]['bytes'] - old_info[nic]["tx"]['bytes'], 
                    "drop": new_info[nic]["tx"]['drop'] - old_info[nic]["tx"]['drop'],
                    "err": new_info[nic]["tx"]['err'] - old_info[nic]["tx"]['err']
                    }
            }
    return ret


if __name__ == '__main__':
    old_info = get_vm_cpu_info()
    time.sleep(10)
    new_info = get_vm_cpu_info()
    print old_info
    print new_info
    print float(new_info['585189ac-e6d0-4bc6-bef1-64bfac9b11f6'] - old_info['585189ac-e6d0-4bc6-bef1-64bfac9b11f6']) / (1000000000 * 4.0 * 10)
