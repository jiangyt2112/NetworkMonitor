#!/usr/bin/python2
import __init__
import json
import commands
from utils.log import SELOG, SERVERLOG

def exe(cmd):
	ret, result = commands.getstatusoutput(cmd)
	if ret == 0:
		return True, result
	else:
		return False, result


def addr_delay(addr):
	print type(addr)
	print addr
	if addr['dhcp_netns'] != None:
		cmd = "ip netns exec %s python test_delay.py %s" %(addr['dhcp_netns'], addr['addr'])
		ret, info = exe(cmd)
	else:
		cmd = "python test_delay.py %s" %(addr['addr'])
		ret, info = exe(cmd)
	if ret == False:
		SERVERLOG.info("server.func.addr_delay - cmd:%s return error, %s." %(cmd, info))
		addr['performance']['error_msg'] = "can't get delay info."
	else:
		info = info[1: -1].split(',')
		try:
			info[0] = int(info[0])
			info[1] = float(info[1])
			info[2] = float(info[2])
		except Exception, e:
			print "ERROR: "info
			print str(e)
			addr['performance']['error_msg'] = "data formate error."
			return
		else:
			addr['performance']['delay'] = info
			print info

def check_delay(result):
	#result = {
	#     "project": self.project,
	#     "req_id": self.req_id,
	#     "item_num": items["item_num"],
	#     "info": None
	# }

	# info = [info]
	    # info struct
	# {
	#     "vm_num": 0,
	#     "host": "ip_addr",
	#     "is_network_node": False,
	#     "topo": "topo_struct"
	# }
	node = result['info'][0]
	for key in node:
		print key + " "

	for node in result['info']:
		for dev in node['topo']['device']:
			if dev['type'] == "virtual host":
				for net in dev['addresses']:
					for addr in dev['addresses'][net]:
						addr_delay(addr)
			else:
				for addr in dev['addresses']:
					addr_delay(addr)