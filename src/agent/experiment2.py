#!/usr/bin/python2
from libvirt_func import get_nic_netinfo
from libvirt_func import get_vm_port_netinfo
from ovs.bridge import get_port_netstats
from func import is_network_node
import time
import json
import commands
import psutil

def exe(cmd):
	ret, result = commands.getstatusoutput(cmd)
	if ret == 0:
		return True, result
	else:
		return False, result

def get_vm_port(dev, vm_port_netstats):
	dev['perf'] = {
            "rx": {"packets": vm_port_netstats[dev['name']]['rd_pkts'], 
                    "bytes": vm_port_netstats[dev['name']]['rd_bytes'], 
                    "drop": vm_port_netstats[dev['name']]['rd_drop'],
                    "err": vm_port_netstats[dev['name']]['rd_err']
                    },
            "tx": {"packets": vm_port_netstats[dev['name']]['wr_pkts'], 
                    "bytes": vm_port_netstats[dev['name']]['wr_bytes'], 
                    "drop": vm_port_netstats[dev['name']]['wr_drop'],
                    "err": vm_port_netstats[dev['name']]['wr_err']
                    }
                }
	return dev

def get_nic_port(dev, nic_port_bandwidth):
	dev['perf'] = nic_port_bandwidth[dev['name']]
	return dev

def get_ovs_port(dev):
	stat = get_port_netstats(dev['name'])
	dev['perf'] = {
            "rx": {"packets":  stat["rx"]['packets'], 
                    "bytes": stat["rx"]['bytes'], 
                    "drop": stat["rx"]['drop'],
                    "err": stat["rx"]['err']
                    },
            "tx": {"packets": stat["tx"]['packets'], 
                    "bytes": stat["tx"]['bytes'], 
                    "drop": stat["tx"]['drop'],
                    "err": stat["tx"]['err']
                }
        	}
	return dev


def memory_usage():
	phymem = psutil.virtual_memory()
	line = "Memory: %5s%% %6s/%s" %(
            phymem.percent,
            str(int(phymem.used/1024/1024))+"M",
            str(int(phymem.total/1024/1024))+"M"
            )
	return line

def getProcess(pName):
	all_pids  = psutil.pids()
	process = None

	for pid in all_pids:
		p = psutil.Process(pid)
		if (p.name() == pName):
			process = p

	return process

def get_delay(dev):
	cmd = "ip netns exec %s python test_delay.py %s" %(dev['name'], dev['addr'])
	ret, info = exe(cmd)
	dev['perf'] = None
	if ret == False:
		print "can't get delay info."
	else:
		info = info[1: -1].split(',')
		try:
			info[0] = int(info[0])
			info[1] = float(info[1])
			info[2] = float(info[2])
		except Exception, e:
			print "ERROR: " + info
			print str(e)
		else:
			dev['perf'] = info
	return dev

def get_once():
	dev_list = None
	nic_port_bandwidth = get_nic_netinfo()
	vm_port_netinfo = get_vm_port_netinfo()
	if is_network_node():
		dev_list = [
			{'type': 'vm_port', 'name': 'fa:16:3e:03:f1:60'},
			{'type': 'nic', 'name': 'tape5abd65e-b4'},
			{'type': 'nic', 'name': 'qvbe5abd65e-b4'},
			{'type': 'nic', 'name': 'qvoe5abd65e-b4'},
			{'type': 'ovs', 'name': 'qvoe5abd65e-b4'},
			{'type': 'ovs', 'name': 'patch-tun'},
			{'type': 'ovs', 'name': 'patch-int'},
			{'type': 'ovs', 'name': 'vxlan-c0a89062'},
			{'type': 'nic', 'name': 'vxlan_sys_4789'},
			{'type': 'nic', 'name': 'ens4'},
			{'type': 'delay', 'name': 'qdhcp-44609914-f133-4f66-bc6e-e16ecce7beec', 'addr': '192.168.1.3'}
			]
	else:
		dev_list = [
			{'type': 'nic', 'name': 'ens4'},
			{'type': 'nic', 'name': 'vxlan_sys_4789'},
			{'type': 'ovs', 'name': 'vxlan-c0a89009'},
			{'type': 'ovs', 'name': 'patch-int'},
			{'type': 'ovs', 'name': 'patch-tun'},
			{'type': 'ovs', 'name': 'qvoaddfe2a4-7c'},
			{'type': 'nic', 'name': 'qvoaddfe2a4-7c'},
			{'type': 'nic', 'name': 'qvbaddfe2a4-7c'},
			{'type': 'nic', 'name': 'tapaddfe2a4-7c'},
			{'type': 'vm_port', 'name': 'fa:16:3e:7b:e3:9d'}
			]
	result = []
	for dev in dev_list:
		if dev['type'] == 'vm_port':
			ret = get_vm_port(dev, vm_port_netinfo)
		elif dev['type'] == 'nic':
			ret = get_nic_port(dev, nic_port_bandwidth)
		elif dev['type'] == 'ovs':
			ret = get_ovs_port(dev)
		elif dev['type'] == 'delay':
			ret = get_delay(dev)
		else:
			print "error dev type: %s" %(dev['type'])
			continue
		result.append(ret)
	return result
def sub(dev1, dev2):
	dev2['perf']['rx']['packets'] -= dev1['perf']['rx']['packets']
	dev2['perf']['rx']['bytes'] -= dev1['perf']['rx']['bytes'] 
	dev2['perf']['rx']['drop'] -= dev1['perf']['rx']['drop']
	dev2['perf']['rx']['err'] -= dev1['perf']['rx']['err']
	dev2['perf']['tx']['packets'] -= dev1['perf']['tx']['packets']
	dev2['perf']['tx']['bytes'] -= dev1['perf']['tx']['bytes']
	dev2['perf']['tx']['drop'] -= dev1['perf']['tx']['drop']
	dev2['perf']['tx']['err'] -= dev1['perf']['tx']['err']
	return dev2
 
def process_result(old_list, new_list):
	ret = []
	for i in range(len(old_list)):
		if old_list[i]['type'] != 'delay':
			ret.append(sub(old_list[i], new_list[i]))
		else:
			ret.append(old_list[i])
			ret.append(new_list[i])
	return ret

def experiment(bond, seconds):
	start = time.time()
	ovs = getProcess("ovs-vswitchd")
	qemu = getProcess("qemu-kvm")
	psutil.cpu_percent(None)
	ovs.cpu_percent(None)
	qemu.cpu_percent(None)

	name = bond + ".txt"
	fp = open(name, 'w')
	fp.write("iperf test: last %s seconds.\n" %(seconds))

	old_list = get_once()
	time.sleep(seconds)
	new_list = get_once()
	result_list = process_result(old_list, new_list)

	stop = time.time()
	cup_per = psutil.cpu_percent(None)
	mem_usg = memory_usage()
	ovs_usg = "%d%%(%dM)" %(ovs.memory_percent(), ovs.memory_info().rss / 1024 / 1024)
	qemu_usg = "%d%%(%dM)" %(qemu.memory_percent(), qemu.memory_info().rss / 1024 / 1024)
	ovs_cpu = ovs.cpu_percent(None)
	qemu_cpu = qemu.cpu_percent(None)
	last = stop - start
	fp.write("start:%s\t" %(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start))))
	fp.write("stop:%s\t" %(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stop))))
	fp.write("last:%d:%d:%d\n" %(last / 3600, (last % 3600) / 60, last % 60))
	fp.write("CPU: %d%%\t%s\tOVS CPU: %d%%\t OVS Memory: %s\t QEMU CPU: %d%%\tQEMU Memory: %s\n" 
		%(cup_per, mem_usg, ovs_cpu, ovs_usg, qemu_cpu, qemu_usg))
	for result in result_list:
		result_str = "%-8s%-20s%-s\n" %(result['type'], result['name'][:20], json.dumps(result['perf']))
		fp.write(result_str)
	fp.close()


import sys
if __name__ == '__main__':
	if len(sys.argv) == 1:
		experiment("1M", 60)
	elif len(sys.argv) == 2:
		experiment(sys.argv[1], 60)
	else:
		experiment(sys.argv[1], int(sys.argv[2]))