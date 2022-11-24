# This code is part of the Advanced Computer Networks (2020) course at Vrije 
# Universiteit Amsterdam.

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

from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase
from ryu.lib.packet import ethernet, ether_types

import topo


class FTRouter(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(FTRouter, self).__init__(*args, **kwargs)
        self.topo_net = topo.Fattree(4)

        self.routing_table = {}

        k = self.topo_net.num_ports

        # lower pod switches
        for pod_num in range(0, k):
            for switch_no in range(0, int(k / 2)):
                ip = '10.' + str(pod_num) + '.' + str(switch_no) + '.1'
                self.routing_table.setdefault(ip, {})

                for host in range(2, int(k / 2) + 2):
                    mask = '10.' + str(pod_num) + '.' + str(switch_no) + '.' + str(host) + '/32'
                    self.routing_table[ip][mask] = host - 1

                self.routing_table[ip].setdefault('0.0.0.0/0', {})

                for host in range(2, int(k / 2) + 2):
                    mask = '0.0.0.' + str(host) + '/8'
                    port = int(((host - 2 + switch_no) % int(k / 2)) + int(k / 2)) + 1
                    self.routing_table[ip]['0.0.0.0/0'][mask] = port

        # upper pod switches
        for pod_num in range(0, k):
            for switch_no in range(int(k / 2), k):
                ip = '10.' + str(pod_num) + '.' + str(switch_no) + '.1'
                self.routing_table.setdefault(ip, {})

                for subnet_no in range(0, int(k / 2)):
                    mask = '10.' + str(pod_num) + '.' + str(subnet_no) + '.0/24'
                    self.routing_table[ip][mask] = subnet_no + 1

                self.routing_table[ip].setdefault('0.0.0.0/0', {})

                for host in range(2, int(k / 2) + 2):
                    mask = '0.0.0.' + str(host) + '/8'
                    port = int(((host - 2 + switch_no) % int(k / 2)) + int(k / 2)) + 1
                    self.routing_table[ip]['0.0.0.0/0'][mask] = port

        # core switches
        for j in range(1, int(k / 2) + 1):
            for i in range(1, int(k / 2) + 1):
                ip = '10.' + str(k) + '.' + str(j) + '.' + str(i)
                self.routing_table.setdefault(ip, {})

                for dest_pod in range(0, k):
                    mask = '10.' + str(dest_pod) + '.0.0/16'
                    self.routing_table[ip][mask] = dest_pod + 1

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):

        # Switches and links in the network
        switches = get_switch(self, None)
        links = get_link(self, None)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install entry-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    # Add a flow entry to the flow-table
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Construct flow_mod message and send it
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # TODO: handle new packets at the controller

        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)

        eth = pkt.get_protocol(ethernet.ethernet)
        dst = eth.dst

        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ip4_pkt = pkt.get_protocol(ipv4.ipv4)
            # src_ip = ip4_pkt.src
            dst_ip = ip4_pkt.dst
            # self.logger.info('  ------SW dpid' + str(dpid))
            # self.logger.info('  _in port: ' + str(in_port))
            # self.logger.info('  _packet_in_handler: %s' % ip4_pkt)
            # self.logger.info('  _src ip: ' + str(src_ip))
            # self.logger.info('  _dst ip: ' + str(dst_ip))
            # self.logger.info('  ------')
        elif eth.ethertype == ether_types.ETH_TYPE_ARP:
            arp_pkt = pkt.get_protocol(arp.arp)
            # src_ip = arp_pkt.src_ip
            dst_ip = arp_pkt.dst_ip
            # self.logger.info('  ------SW dpid' + str(dpid))
            # self.logger.info('  _in port: ' + str(in_port))
            # self.logger.info('  _packet_in_handler: %s' % arp_pkt)
            # self.logger.info('  _src ip: ' + str(src_ip))
            # self.logger.info('  _dst ip: ' + str(dst_ip))
            # self.logger.info('  ------')
        else:
            return

        switch = next(s for s in self.topo_net.switches if (s.dpid[1:] == str(dpid)))
        out_port = None

        for prefix, port_value in self.routing_table[switch.id].items():
            how_many_matching_bits = int(int(prefix.split('/')[1]) / 8)
            prefix = prefix.split('/')[0]

            if how_many_matching_bits == 0:
                for suffix, port in port_value.items():
                    how_many_matching_bits = int(int(suffix.split('/')[1]) / 8)
                    suffix = suffix.split('/')[0]

                    if dst_ip.split('.')[-how_many_matching_bits:] == suffix.split('.')[-how_many_matching_bits:]:
                        out_port = port
                        break

            if dst_ip.split('.')[:how_many_matching_bits] == prefix.split('.')[:how_many_matching_bits]:
                out_port = port_value
                break

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if eth.ethertype == ether_types.ETH_TYPE_IP:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            self.add_flow(datapath, 1, match, actions)

        # Construct packet_out message and send it
        out = parser.OFPPacketOut(datapath=datapath,
                                  in_port=in_port,
                                  actions=actions,
                                  buffer_id=ofproto.OFP_NO_BUFFER,
                                  data=msg.data)
        datapath.send_msg(out)
