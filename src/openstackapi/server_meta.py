{
	'OS-EXT-STS:task_state': None, 
	'addresses': 
		{'int-net': 
			[
				{'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:5d:9e:22', 
				'version': 4, 
				'addr': '192.168.1.8', 
				'OS-EXT-IPS:type': 'fixed'
				}, 
				{'OS-EXT-IPS-MAC:mac_addr': 'fa:16:3e:5d:9e:22', 
				'version': 4, 
				'addr': '192.168.166.23', 
				'OS-EXT-IPS:type': 'floating'
				}
			]
		}, 
	'OS-EXT-STS:vm_state': 'active',
	'OS-EXT-SRV-ATTR:instance_name': 'instance-00000002', 
	'OS-SRV-USG:launched_at': '2018-10-26T09:36:46.000000', 
	
	'id': '61205745-b2bf-4db0-ad50-e7a60bf08bd5', 
	'security_groups': [{'name': 'defalt'}], 
	'user_id': 'd2fcc0c45a134de28dba429dbef2c3ba', 
	'progress': 0, 
	'OS-EXT-STS:power_state': 1, 
	'OS-EXT-AZ:availability_zone': 'nova', 
	'status': 'ACTIVE', 
	'updated': '2018-10-26T09:36:46Z', 
	'hostId': '1b6fa73a7ea8e40dc812954fe751d3aa812e6b52489ddb5360f5d36e', 
	'OS-EXT-SRV-ATTR:host': 'control-node', 
	'OS-SRV-USG:terminated_at': None, 
	'OS-EXT-SRV-ATTR:hypervisor_hostname': 'control-node', 
	'name': 'test', 
	'created': '2018-10-26T09:36:38Z', 
	'tenant_id': 'a95424bbdca6410092073d564f1f4012', 
}
# ip netns add ns1
# ovs-vsctl add-port br-int tap0 tag=1 -- set Interface tap0 type=internal
# ip a
# ovs-vsctl show
# ip link set tap0  netns ns1
# ip netns exec ns1 ip addr add 192.168.1.3/24 dev tap0
# ip netns exec ns1 ifconfig tap0 promisc up
# ip netns exec ns1 ip a
# ip netns exec ns1 ping 192.168.1.1

# ip netns add ns1
# ip netns show
# ip netns exec ns1 ip a
# ip netns exec ns1 ip tuntap add tap0 mode tap
# ip netns exec ns1 ip a
# ip netns exec ns1 ip aadr add 192.168.1.3/24 dev tap0
# ip netns exec ns1 ip addr add 192.168.1.3/24 dev tap0
# ip netns exec ns1 ip a
# ip netns exec ns1 ip set tap0 up
# ip netns exec ns1 ip link set tap0 up


# ovs-ofctl dump-ports br-int qvo3ef787ad-67
# ovs-vsctl list interface br-ex


