{
	'br-tun': 
		{
			'Controller': ['tcp:127.0.0.1:6633'], 
			'fail_mode': 'secure', 
			'Port': 
				{
					'br-tun':
						{
							'intf': 'br-tun', 
							'vlan': '', 
							'type': 'internal'
						}, 
					'patch-int': 
						{
							'intf': 'patch-int', 
							'vlan': '', 
							'type': 'patch'
						}, 
					'vxlan-c0a89062': 
						{
							'intf': 'vxlan-c0a89062', 
							'vlan': '', 
							'type': 'vxlan'
						}
					}
				}, 
	'br-int': 
		{
			'Controller': ['tcp:127.0.0.1:6633'], 
			'fail_mode': 'secure', 
			'Port': 
				{
					'qg-b8cfeaad-ef': 
						{
							'intf': 'qg-b8cfeaad-ef', 
							'vlan': '2', 
							'type': 'internal'
						}, 
					'patch-tun': 
						{
							'intf': 'patch-tun', 
							'vlan': '', 
							'type': 'patch'
						}, 
					'qvo3ef787ad-67': 
						{
							'intf': 'qvo3ef787ad-67', 
							'vlan': '1', 
							'type': ''
						}, 
					'br-int': 
						{
							'intf': 'br-int', 
							'vlan': '', 
							'type': 'internal'
						}, 
					'qr-661bb3c3-36': 
						{
							'intf': 'qr-661bb3c3-36', 
							'vlan': '1', 
							'type': 'internal'
						}, 
					'int-br-ex': 
						{
							'intf': 'int-br-ex', 
							'vlan': '', 
							'type': 'patch'
						}, 
					'tap3e25711d-88': 
						{
							'intf': 'tap3e25711d-88', 
							'vlan': '1', 
							'type': 'internal'
						}, 
					'qvo879f22e7-61': 
						{
							'intf': 'qvo879f22e7-61', 
							'vlan': '1', 
							'type': ''
						}
				}
		}, 
	'br-ex': 
		{
			'Controller': ['tcp:127.0.0.1:6633'], 
			'fail_mode': 'secure', 
			'Port': 
				{
					'ens5': 
						{
							'intf': 'ens5', 
							'vlan': '', 
							'type': ''
						}, 
					'phy-br-ex': 
						{
							'intf': 'phy-br-ex', 
							'vlan': '', 
							'type': 'patch'
						}, 
					'br-ex': 
						{
							'intf': 'br-ex', 
							'vlan': '', 
							'type': 'internal'
						}
				}
		}
}
