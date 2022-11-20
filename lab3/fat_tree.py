# This code is part of the Advanced Computer Networks (ACN) course at VU 
# Amsterdam.

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#   http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

#!/usr/bin/env python3

# A dirty workaround to import topo.py from lab2

import os
import subprocess
import time

import mininet
import mininet.clean
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import lg, info
from mininet.link import TCLink
from mininet.node import Node, OVSKernelSwitch, RemoteController
from mininet.topo import Topo
from mininet.util import waitListening, custom

import topo

class FattreeNet(Topo):
    """
    Create a fat-tree network in Mininet
    """

    def __init__(self, ft_topo):
        
        Topo.__init__(self)

        # TODO: please complete the network generation logic here
        self.servers = ft_topo.servers
        self.num_ports = ft_topo.num_ports
        self.core_switches = [switch for switch in ft_topo.switches if switch.type == 'c_sw']
        self.pod_switches = [switch for switch in ft_topo.switches if switch.type == 'p_sw']
        modulo_values = [n for n in range(int(self.num_ports / 2))]
        self.lower_pod_switches = [switch for idx, switch in enumerate(self.pod_switches) if
                              idx % self.num_ports in modulo_values]
        self.upper_pod_switches = [switch for switch in self.pod_switches if switch not in self.lower_pod_switches]
        self.generate()


    def dpid(self, core=None, pod=None, switch=None):
        if core is not None:
            return '0000000010%02x0000'%core
        else:
            return'000000002000%02x%02x'%(pod, switch)

    def get_pod_num(self, ip):
        _, pod, _, _ = ip.split(".")
        return int(pod)

    def generate(self):
        core_switches = []
        upper_switches = []
        lower_switches = []
        servers =  []

        #adding switches and servers to mininet
        for i, core_switch in enumerate(self.core_switches):
            print(self.dpid(core=i))
            core_switches.append(self.addSwitch("c_sw{}".format(i), dpid=self.dpid(core=i)))

        for i, upper_switch in enumerate(self.upper_pod_switches):
            upper_switches.append(self.addSwitch("u_sw{}".format(i), dpid=self.dpid(switch=i, pod=self.get_pod_num(upper_switch.id))))
                
        for i, lower_switch in enumerate(self.lower_pod_switches):
            lower_switches.append(self.addSwitch("l_sw{}".format(i), dpid=self.dpid(switch=i, pod=self.get_pod_num(lower_switch.id))))

        for i, server in enumerate(self.servers):
            servers.append(self.addHost("s{}".format(i), ip=server.id))


        linked_edges = []
        #creating links between core layer and upper layer
        for core_switch in self.core_switches:
            for edge in core_switch.edges:
                pod_switch = edge.rnode
                core_switch_idx = self.core_switches.index(core_switch)
                pod_switch_idx = self.upper_pod_switches.index(pod_switch)
                self.addLink(core_switches[core_switch_idx], upper_switches[pod_switch_idx], bw=15, delay='5ms')
                linked_edges.append(edge)
        
        #creating links upper layer and lower layer
        for upper_switch in self.upper_pod_switches:
            for edge in upper_switch.edges:
                if edge not in linked_edges:
                    lower_switch = edge.lnode
                    upper_switch_idx = self.upper_pod_switches.index(upper_switch)
                    lower_switch_idx = self.lower_pod_switches.index(lower_switch)
                    self.addLink(upper_switches[upper_switch_idx], lower_switches[lower_switch_idx], bw=15, delay='5ms')
                    linked_edges.append(edge)

        #creating links between lower layer and servers
        for server in self.servers:
            for edge in server.edges:
                switch = edge.rnode
                server_idx = self.servers.index(server)
                switch_idx = self.lower_pod_switches.index(switch)
                self.addLink(lower_switches[switch_idx], servers[server_idx], bw=15, delay='5ms')
                linked_edges.append(edge)


def make_mininet_instance(graph_topo):

    net_topo = FattreeNet(graph_topo)
    net = Mininet(topo=net_topo, controller=None, autoSetMacs=True)
    net.addController('c0', controller=RemoteController, ip="127.0.0.1", port=6653)
    return net

def run(graph_topo):
    
    # Run the Mininet CLI with a given topology
    lg.setLogLevel('info')
    mininet.clean.cleanup()
    net = make_mininet_instance(graph_topo)

    info('*** Starting network ***\n')
    net.start()
    info('*** Running CLI ***\n')
    CLI(net)
    info('*** Stopping network ***\n')
    net.stop()



ft_topo = topo.Fattree(4)

run(ft_topo)
