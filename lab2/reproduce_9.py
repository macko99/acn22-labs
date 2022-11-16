# This code is part of the Advanced Computer Networks course at Vrije
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

import topo
import numpy as np
import matplotlib.pyplot as plt

# # Setup for Jellyfish
# num_servers = 686
# num_switches = 245
# num_ports = 14

# jf_topo = topo.Jellyfish(num_servers, num_switches, num_ports)

# TODO: code for reproducing Figure 9 in the jellyfish paper

if __name__ == "__main__":

    num_ports = 4
    num_servers = int((num_ports ** 3) / 4)
    num_switches = int(num_ports * num_ports * 5 / 4)

    jf_topo = topo.Jellyfish(num_servers, num_switches, num_ports)

    # EXAMPLE
    result = topo.ksp_yen(jf_topo.switches + jf_topo.servers, jf_topo.servers[0], jf_topo.servers[5], 8)
    for route in result:
        print(str(route['cost']) + ': ', end='')
        for node in route['path']:
            print(str(node.type) + str(node.id) + ' -> ', end='')
        print('')

    # links = {}
    # counter = []
    # jf_server_ids = [server.id for server in jf_topo.servers]
    # jf_server_id_pairs = [(a, b) for idx, a in enumerate(jf_server_ids) for b in jf_server_ids[idx + 1:]]
    # jf_server_links = [(a, b) for idx, a in enumerate(jf_topo.servers) for b in jf_topo.servers[idx + 1:]]

    # for idx, pair in enumerate(jf_server_links):
    #     part_result = topo.ksp_yen(jf_topo.switches + jf_topo.servers, pair[0], pair[1], 8)
    #     links[jf_server_id_pairs[idx]] = [x['cost'] for x in part_result]
    #     counter.append(len(links[jf_server_id_pairs[idx]]))

    # print(links)
    # print(counter)
    # print(len(counter))

    # ft_server_next_hop_id_list = [server.edges[0].rnode.id for server in ft_topo.servers]
    # ft_server_next_hop_pairs = \
    #     [(a, b) for idx, a in enumerate(ft_server_next_hop_id_list) for b in ft_server_next_hop_id_list[idx + 1:]]

    # for pair in ft_server_next_hop_pairs:
    #     distance = distance_ft[pair] + 2
    #     ft_distribution[distance] += 1
