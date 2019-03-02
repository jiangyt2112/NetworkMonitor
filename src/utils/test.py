
from itertools import chain
from ovs import ovsdb
from ovs.utils import execute
from ovs.utils import decorator

def show_br(self):
    brs, br = {}, ''
    cmd = 'ovs-vsctl show'
    result, error = execute.exec_cmd(cmd)
    if error:
        return {}
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
    return brs

if __name__ == '__main__':
    print show_br()