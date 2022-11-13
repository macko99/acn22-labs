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
import queue
import numpy as np
import matplotlib.pyplot as plt

# # Same setup for Jellyfish and Fattree
# num_servers = 686
# num_switches = 245
# num_ports = 14

# ft_topo = topo.Fattree(num_ports)
# jf_topo = topo.Jellyfish(num_servers, num_switches, num_ports)

# TODO: code for reproducing Figure 1(c) in the jellyfish paper

class Prioritize(object):
    def __init__(self, priority, object):
        self.priority = priority
        self.object = object
    def __lt__(self, other):
        return self.priority<other.priority


def dijkstra(start_vertex, verticies):
        result = {}
        for switch in verticies:
            result[switch] = float('inf')
        result[start_vertex] = 0
        visited = []

        p_queue = queue.PriorityQueue()
        p_queue.put(Prioritize(0, start_vertex))

        while not p_queue.empty():
            current_vertex = p_queue.get().object
            visited.append(current_vertex)

            for neighbor in verticies:
                if current_vertex.is_neighbor(neighbor):
                    distance = 1
                    if neighbor not in visited:
                        old_cost = result[neighbor]
                        new_cost = result[current_vertex] + distance
                        if new_cost < old_cost:
                            p_queue.put(Prioritize(new_cost, neighbor))
                            result[neighbor] = new_cost
        return result

if __name__ == "__main__":

    num_ports = 14
    num_servers = int((num_ports**3)/4)
    num_switches = int(num_ports*num_ports*5/4)

    ft_distribution = [0] * 10
    jf_distribution = [0] * 10

    #_____________FATTREE___________________

    ft_topo = topo.Fattree(num_ports)

    distance_ft = {}
    for start_switch in ft_topo.switches:
        part_distance = dijkstra(start_switch, ft_topo.switches)
        for end_switch in part_distance:
            distance_ft[(start_switch.id, end_switch.id)] = part_distance[end_switch]

    ft_server_next_hop_id_list = [server.edges[0].rnode.id for server in ft_topo.servers]
    ft_server_next_hop_pairs = [(a, b) for idx, a in enumerate(ft_server_next_hop_id_list) for b in ft_server_next_hop_id_list[idx + 1:]]

    for pair in ft_server_next_hop_pairs:
        distance = distance_ft[pair] + 2
        ft_distribution[distance] += 1

    #_____________JELLYFISH___________________

    for _ in range(10): #10 times in paper
        jf_topo = topo.Jellyfish(num_servers, num_switches, num_ports)

        distance_jf = {}
        for start_switch in jf_topo.switches:
            part_distance = dijkstra(start_switch, jf_topo.switches)
            for end_switch in part_distance:
                distance_jf[(start_switch.id, end_switch.id)] = part_distance[end_switch]

        jf_server_next_hop_id_list = [server.edges[0].rnode.id for server in jf_topo.servers]
        jf_server_next_hop_pairs = [(a, b) for idx, a in enumerate(jf_server_next_hop_id_list) for b in jf_server_next_hop_id_list[idx + 1:]]

        for pair in jf_server_next_hop_pairs:
            distance = distance_jf[pair] + 2
            jf_distribution[distance] += 1

    #_____________PLOTTING___________________

    ft_fractions = ft_distribution[2:7]
    ft_fractions = [num/sum(ft_fractions) for num in ft_fractions]
   
    jf_fractions = jf_distribution[2:7]
    jf_fractions = [num/sum(jf_fractions) for num in jf_fractions]

    labels = ['2', '3', '4', '5', '6']
    x = np.arange(len(labels))  # the label locations
    width = 0.3  # the width of the bars

    fig, ax = plt.subplots()
    rects1 = ax.bar(x - width/2, jf_fractions, width, label='JellyFish')
    rects2 = ax.bar(x + width/2, ft_fractions, width, label='FatTree')

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Fraction of Server Pairs')
    ax.set_xlabel('Path length')
    ax.set_xticks(x, labels)
    ax.legend()
        
    fig.tight_layout()
    plt.ylim([0,1])

    plt.savefig('fig_1c_k' + str(num_ports) + '.png')
    # plt.show()

    plt.clf()
    fig.clf()

