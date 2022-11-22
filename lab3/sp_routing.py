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


class SPRouter(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SPRouter, self).__init__(*args, **kwargs)

        self.topo_net = topo.Fattree(4)
        self.shortest_paths = {}
        self.known_hosts = []
        self.ip_to_port = {}
        self.topo_raw_links = []

        for start_host in self.topo_net.servers:
            part_distance, part_path = topo.dijkstra(start_host, self.topo_net.switches + self.topo_net.servers)
            for end_host in part_distance:
                if end_host.type == 'h' and start_host != end_host:
                    self.shortest_paths[(start_host.id, end_host.id)] = topo.get_path_dpid(part_path, start_host, end_host)


    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):

        # Switches and links in the network
        # self.topo_raw_switches = get_switch(self, None)
        self.topo_raw_links = get_link(self, None)

    def route(self, ev, src_ip, dst_ip):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)

        eth = pkt.get_protocol(ethernet.ethernet)
        dst = eth.dst

        link_port = {link.dst.dpid: link.src.port_no for link in self.topo_raw_links if link.src.dpid == dpid}
        
        path = self.shortest_paths[(src_ip, dst_ip)][1:]

        for i, switch in enumerate(path):
            if switch == dpid:
                if i + 2 < len(path):
                    # next hop is another switch - lets go there
                    next_hop = path[i + 1]  # dpid of next switch
                    out_port = link_port[next_hop]

                    actions = [parser.OFPActionOutput(out_port)]

                    # install a flow to avoid packet_in next time
                    if out_port != ofproto.OFPP_FLOOD and eth.ethertype == ether_types.ETH_TYPE_IP:
                        match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
                        self.add_flow(datapath, 1, match, actions)

                    # Construct packet_out message and send it
                    out = parser.OFPPacketOut(datapath=datapath,
                                              in_port=in_port,
                                              actions=actions,
                                              buffer_id=datapath.ofproto.OFP_NO_BUFFER,
                                              data=msg.data)
                    datapath.send_msg(out)
                    return
                else:
                    # next hop is host, we are the last switch on path
                    if dst_ip in self.ip_to_port[dpid]:
                        out_port = self.ip_to_port[dpid][dst_ip]
                        actions = [parser.OFPActionOutput(out_port)]

                        # install a flow to avoid packet_in next time
                        if out_port != ofproto.OFPP_FLOOD and eth.ethertype == ether_types.ETH_TYPE_IP:
                            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
                            self.add_flow(datapath, 1, match, actions)

                        # Construct packet_out message and send it
                        out = parser.OFPPacketOut(datapath=datapath,
                                                  in_port=in_port,
                                                  actions=actions,
                                                  buffer_id=datapath.ofproto.OFP_NO_BUFFER,
                                                  data=msg.data)
                        datapath.send_msg(out)
                        return
                    else:
                        # out_port = ofproto.OFPP_FLOOD
                        self.logger.info('  _CANNOT FIND HOST -> %s' % dst_ip)

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

        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)

        eth = pkt.get_protocol(ethernet.ethernet)

        self.ip_to_port.setdefault(dpid, {})

        if eth.ethertype == ether_types.ETH_TYPE_IP:
            ip4_pkt = pkt.get_protocol(ipv4.ipv4)
            src_ip = ip4_pkt.src
            dst_ip = ip4_pkt.dst

            # self.logger.info("  ------SW dpid" + str(dpid))
            # self.logger.info("  _in port: " + str(in_port))
            # self.logger.info('  _packet_in_handler: src_mac -> %s' % src)
            # self.logger.info('  _packet_in_handler: dst_mac -> %s' % dst)
            # self.logger.info('  _packet_in_handler: %s' % ip4_pkt)
            # self.logger.info("  _src ip: " + str(src_ip))
            # self.logger.info("  _dst ip: " + str(dst_ip))
            # self.logger.info('  ------')

            self.route(ev, src_ip, dst_ip)

        if eth.ethertype == ether_types.ETH_TYPE_ARP:

            arp_pkt = pkt.get_protocol(arp.arp)
            src_ip = arp_pkt.src_ip
            dst_ip = arp_pkt.dst_ip

            # self.logger.info("  ------SW dpid" + str(dpid))
            # self.logger.info("  _in port: " + str(in_port))
            # self.logger.info('  _packet_in_handler: src_mac -> %s' % src)
            # self.logger.info('  _packet_in_handler: dst_mac -> %s' % dst)
            # self.logger.info('  _packet_in_handler: %s' % ip4_pkt)
            # self.logger.info("  _src ip: " + str(src_ip))
            # self.logger.info("  _dst ip: " + str(dst_ip))
            # self.logger.info('  ------')

            self.ip_to_port[dpid][src_ip] = in_port

            if src_ip not in self.known_hosts:
                self.known_hosts.append(src_ip)

            if dst_ip not in self.known_hosts:
                actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
                # Construct packet_out message and send it
                out = parser.OFPPacketOut(datapath=datapath,
                                          in_port=in_port,
                                          actions=actions,
                                          buffer_id=datapath.ofproto.OFP_NO_BUFFER,
                                          data=msg.data)
                datapath.send_msg(out)
            else:
                self.route(ev, src_ip, dst_ip)
