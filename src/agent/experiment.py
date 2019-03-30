#!/usr/bin/python2
import __init__
from func import ping_test
from libvirt_func import get_nic_netstats
from libvirt_func import get_vm_port_netstats
from ovs.bridge import get_port_netstats
from func import is_network_node
import time
import json

def exe(cmd):
	ret, result = commands.getstatusoutput(cmd)
	if ret == 0:
		return True, result
	else:
		return False, result

def get_vm_port(dev):
	all_ = get_vm_port_netstats()
	dev['perf'] = all_[dev['name']]
	return dev

def get_nic_port(dev, nic_port_bandwidth):
	dev['perf'] = nic_port_bandwidth[dev['name']]
	return dev

def get_ovs_port(dev):
	dev['perf'] = get_port_netstats(dev['name'])
	return dev

def get_delay(dev):
	cmd = "ip netns exec %s python test_delay.py %s" %(dev['name'], addr['addr'])
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

def experiment_once():
	dev_list = None
	nic_port_bandwidth = get_nic_netstats()
	if is_network_node():
		dev_list = [
			{'type': 'vm_port', 'name': 'fa:16:3e:03:f1:60'},
			{'type': 'nic', 'name': 'tape5abd65e-b4'},
			{'type': 'nic', 'name': 'qvbe5abd65e-b4'},
			{'type': 'nic', 'name': 'qvoe5abd65e-b4'},
			{'type': 'ovs', 'name': 'qvoe5abd65e-b4'},
			{'type': 'ovs', 'name': 'patch-tun'},
			{'type': 'ovs', 'name': 'patch-int'},
			{'type': 'nic', 'name': 'ens4'},
			{'type': 'delay', 'name': 'qdhcp-44609914-f133-4f66-bc6e-e16ecce7beec', 'addr': '192.168.1.3'}
			]
	else:
		dev_list = [
			{'type': 'nic', 'name': 'ens4'},
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
			ret = get_vm_port(dev)
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

def add_once(result_list, once):
	for i in range(len(once)):
		if once[i]['type'] != 'delay':
			result_list[i]['perf']['rx']['packets'] += once[i]['perf']['rx']['packets']
			result_list[i]['perf']['rx']['bytes'] += once[i]['perf']['rx']['bytes']
			result_list[i]['perf']['rx']['drop'] += once[i]['perf']['rx']['drop']
			result_list[i]['perf']['tx']['packets'] += once[i]['perf']['tx']['packets']
			result_list[i]['perf']['tx']['bytes'] += once[i]['perf']['tx']['bytes']
			result_list[i]['perf']['tx']['drop'] += once[i]['perf']['tx']['drop']
		else:
			# percent lost packages, max round trip time, avrg round trip
			result_list[i]['perf'][0] += once[i]['perf'][0]
			result_list[i]['perf'][1] += once[i]['perf'][1]
			result_list[i]['perf'][2] += once[i]['perf'][2]

def avg_result(result_list, times):
	for i in result_list:
		if i['type'] != 'delay':
			i['perf']['rx']['packets'] /= times
			i['perf']['rx']['bytes'] /= times
			i['perf']['rx']['drop'] /= times
			i['perf']['tx']['packets'] /= times
			i['perf']['tx']['bytes'] /= times
			i['perf']['tx']['drop'] /= times
		else:
			# percent lost packages, max round trip time, avrg round trip
			i['perf'][0] /= times
			i['perf'][1] /= float(times)
			i['perf'][2] /= float(times)


def experiment(bond, times = 60):
	start = time.time()
	name = bond + ".txt"
	fp = open(name, 'w')
	fp.write("iperf test: occur %s times.\n" %(times))
	result_list = []

	once = experiment_once()
	for i in range(once):
		result_list.append(i)

	for i in range(times - 1):
		once = experiment_once()
		add_once(result_list, once)

	avg_result(result_list, times)

	stop = time.time()
	last = stop - start
	fp.write("start:%s\n" %(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(start))))
	fp.write("stop:%s\n" %(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stop))))
	fp.write("last:%d:%d:%d\n" %(last / 3600, (last % 3600) / 60, last % 60))
	for result in result_list:
		result_str = "%s\t%s\t\t%s\n" %(result['type'], result['name'], json.dumps(result['perf']))
		fp.write(result_str)
	close(fp)

if __name__ == '__main__':
	experiment("1M")

# iperf -f m -i 1 -p 5001 -u -b 1M -c -t 100 (-d)
# iperf -f m -i 1 -p 5001 -u -s -o 1m.txt 