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

# !/usr/bin/env python3

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

    def __init__(self, topo):

        Topo.__init__(self)

        # TODO: please complete the network generation logic here
        net_servers = []
        net_core_switches = []
        net_lower_pod_switches = []
        net_upper_pod_switches = []

        core_switches = [switch for switch in topo.switches if switch.type == 'c_sw']
        pod_switches = [switch for switch in topo.switches if switch.type == 'p_sw']
        modulo_values = [n for n in range(int(topo.num_ports / 2))]
        lower_pod_switches = [switch for idx, switch in enumerate(pod_switches) if
                              idx % topo.num_ports in modulo_values]
        upper_pod_switches = [switch for switch in pod_switches if switch not in lower_pod_switches]

        # adding switches and servers to mininet
        for core_switch in core_switches:
            net_core_switches.append(self.addSwitch(core_switch.dpid))

        for upper_switch in upper_pod_switches:
            net_upper_pod_switches.append(self.addSwitch(upper_switch.dpid))

        for lower_switch in lower_pod_switches:
            net_lower_pod_switches.append(self.addSwitch(lower_switch.dpid))

        for i, server in enumerate(topo.servers):
            net_servers.append(self.addHost("host{}".format(i), ip=server.id))

        linked_edges = []
        # creating links between core layer and upper layer
        for core_switch in core_switches:
            for edge in core_switch.edges:
                pod_switch = edge.rnode
                core_switch_idx = core_switches.index(core_switch)
                pod_switch_idx = upper_pod_switches.index(pod_switch)
                self.addLink(net_core_switches[core_switch_idx],
                             net_upper_pod_switches[pod_switch_idx],
                             bw=15, delay='5ms')
                linked_edges.append(edge)

        # creating links upper layer and lower layer
        for upper_switch in upper_pod_switches:
            for edge in upper_switch.edges:
                if edge not in linked_edges:
                    lower_switch = edge.lnode
                    upper_switch_idx = upper_pod_switches.index(upper_switch)
                    lower_switch_idx = lower_pod_switches.index(lower_switch)
                    self.addLink(net_upper_pod_switches[upper_switch_idx],
                                 net_lower_pod_switches[lower_switch_idx],
                                 bw=15, delay='5ms')

        # creating links between lower layer and servers
        for server in topo.servers:
            for edge in server.edges:
                switch = edge.rnode
                server_idx = topo.servers.index(server)
                switch_idx = lower_pod_switches.index(switch)
                self.addLink(net_lower_pod_switches[switch_idx],
                             net_servers[server_idx],
                             bw=15, delay='5ms')


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
