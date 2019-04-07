# coding=utf-8
import __init__
import commands
import time

def exe(cmd):
    ret, result = commands.getstatusoutput(cmd)
    if ret == 0:
        return True, result
    else:
        return False, result

def get_ovs_info(net_flag = True):
    brs, br = {}, ''
    cmd = 'ovs-vsctl show'
    ret, result = exe(cmd)
    if not ret:
        return ret, "cmd:ovs-vsctl show return error."

    for l in result.split('\n'):
        l = l.strip().replace('"', '')
        if l.startswith('Bridge '):
            br = l.lstrip('Bridge ')
            brs[br] = {}
            brs[br]['Controller'] = []
            brs[br]['Port'] = {}
            brs[br]['fail_mode'] = ''
        else:
            if l.startswith('Controller '):
                brs[br]['Controller'].append(l.replace('Controller ', ''))
            elif l.startswith('fail_mode: '):
                brs[br]['fail_mode'] = l.replace('fail_mode: ', '')
            elif l.startswith('Port '):
                phy_port = l.replace('Port ', '')  # e.g., br-eth0
                brs[br]['Port'][phy_port] = {'vlan': '', 'type': ''}
            elif l.startswith('tag: '):
                brs[br]['Port'][phy_port]['vlan'] = l.replace('tag: ', '')
            elif l.startswith('Interface '):
                brs[br]['Port'][phy_port]['intf'] = \
                    l.replace('Interface ', '')
            elif l.startswith('type: '):
                brs[br]['Port'][phy_port]['type'] = l.replace('type: ', '')
            elif l.startswith('options: '):
                brs[br]['Port'][phy_port]['options'] = l.replace('options: ', '')
    if net_flag:
        get_ovs_port_netstats(brs)
    return True, brs

def get_port_netstats(port):
    netstats = {
        "rx": {"packets": 0, "bytes": 0, "drop": 0},
        "tx": {"packets": 0, "bytes": 0, "drop": 0}
    }
    ret, info = exe("ovs-vsctl list interface %s" %(port))
    if ret == False:
        return netstats

    info = info.split("\n")
    stats = None
    for i in info:
        if i.startswith("statistics"):
            stats = i
    if stats == None:
        return netstats

    stats = stats.split(":")[1].strip()
    stats = stats[1: -1]
    stats = stats.split(",")
    for i in range(len(stats)):
        stats[i] = stats[i].strip()

    s = {}
    for i in stats:
        s[i.split('=')[0]] = int(i.split('=')[1])
    #print port
    #print s

    netstats['rx']['packets'] = s['rx_packets']
    netstats['rx']['bytes'] = s['rx_bytes']
    if 'rx_dropped' in s:
        netstats['rx']['drop'] = s['rx_dropped']
    else:
        netstats['rx']['drop'] = 0
    if 'rx_errors' in s:
        netstats['rx']['err'] = s['rx_errors']
    else:
        netstats['rx']['err'] = 0
    netstats['tx']['packets'] = s['tx_packets']
    netstats['tx']['bytes'] = s['tx_bytes']
    if 'tx_dropped' in s:
        netstats['tx']['drop'] = s['tx_dropped']
    else:
        netstats['tx']['drop'] = 0
    if 'tx_errors' in s:
        netstats['tx']['err'] = s['tx_errors']
    else:
        netstats['tx']['err'] = 0
    return netstats

def get_ovs_port_netstats(brs):
    interfaces = {}
    for bridge in brs:
        for port in brs[bridge]['Port']:
            interfaces[port] = brs[bridge]['Port'][port]

    old_stats = {}
    for port in interfaces:
        old_stats[port] = get_port_netstats(port)
    
    time.sleep(1)

    new_stats = {}
    for port in interfaces:
        new_stats[port] = get_port_netstats(port)

    for port in interfaces:
        interfaces[port]['bandwidth'] = {
            "rx": {"packets": new_stats[port]["rx"]['packets'] - old_stats[port]["rx"]['packets'], 
                    "bytes": new_stats[port]["rx"]['bytes'] - old_stats[port]["rx"]['bytes'], 
                    "drop": new_stats[port]["rx"]['drop'] - old_stats[port]["rx"]['drop'],
                    "err": new_stats[port]["rx"]['err'] - old_stats[port]["rx"]['err']
                    },
            "tx": {"packets": new_stats[port]["tx"]['packets'] - old_stats[port]["tx"]['packets'], 
                    "bytes": new_stats[port]["tx"]['bytes'] - old_stats[port]["tx"]['bytes'], 
                    "drop": new_stats[port]["tx"]['drop'] - old_stats[port]["tx"]['drop'],
                    "err": new_stats[port]["tx"]['err'] - old_stats[port]["tx"]['err']
                }
        }


if __name__ == '__main__':
    print get_ovs_info()
    