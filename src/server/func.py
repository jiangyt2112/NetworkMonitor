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
		ret = ret[1: -1].split(',')
		ret[0] = int(ret[0])
		ret[1] = float(ret[1])
		ret[2] = float(ret[2])
		addr['performance']['delay'] = ret

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
			for addr in dev['addresses']:
				addr_delay(addr)