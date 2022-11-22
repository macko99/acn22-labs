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

import random
import queue
import matplotlib.pyplot as plt
import math


# region Edge
# Class for an edge in the graph
class Edge:
    def __init__(self):
        self.lnode = None
        self.rnode = None

    def remove(self):
        self.lnode.edges.remove(self)
        self.rnode.edges.remove(self)
        self.lnode = None
        self.rnode = None


# endregion

# region Node
# Class for a node in the graph
class Node:
    def __init__(self, id, type, dpid=None):
        self.edges = []
        self.id = id
        self.dpid = dpid
        self.type = type

    # Add an edge connected to another node
    def add_edge(self, node):
        edge = Edge()
        edge.lnode = self
        edge.rnode = node
        self.edges.append(edge)
        node.edges.append(edge)
        return edge

    # Remove an edge from the node
    def remove_edge(self, edge):
        self.edges.remove(edge)

    # Decide if another node is a neighbor
    def is_neighbor(self, node):
        for edge in self.edges:
            if edge.lnode == node or edge.rnode == node:
                return True
        return False

    def find_edge(self, node):
        for edge in self.edges:
            if edge.lnode == node or edge.rnode == node:
                return edge
        return None


# endregion

# region Jellyfish
class Jellyfish:

    def __init__(self, num_servers, num_switches, num_ports):
        self.servers = []
        self.switches = []
        self.num_ports = num_ports
        self.generate(num_servers, num_switches)

    # function creating jellyfish topology following the paper
    def generate(self, num_servers, num_switches):

        switches = []
        open_ports = []
        # Adding switches to topology, incremental id-s.
        for i in range(num_switches):
            switch = Node(i, 'sw')
            switches.append(switch)
            # Setting counter of open ports for this switch to num_ports
            open_ports.append(self.num_ports)

        # Adding servers to topology
        servers = []
        for i in range(num_servers):
            host = Node(i, 'h')
            # Connecting each server to one switch evenly
            switch = switches[i % num_switches]
            host.add_edge(switch)
            # Server was connected to switch, so we decrease number of open ports on switch
            open_ports[i % num_switches] -= 1
            servers.append(host)

        links = []
        switch_idx_list = [n for n in range(num_switches)]
        # We create list of all combinations of switches pairs from the set
        switch_idx_pairs = [(a, b) for idx, a in enumerate(switch_idx_list) for b in switch_idx_list[idx + 1:]]
        # We keep track how many more switches need to be connected
        switch_left = num_switches

        while switch_left > 1 and switch_idx_pairs:
            # Picking random pair of switches
            pair = random.choice(switch_idx_pairs)
            # If both switches have still some open ports we connect them
            if open_ports[pair[0]] > 0 and open_ports[pair[1]] > 0:
                sw1 = switches[pair[0]]
                sw2 = switches[pair[1]]
                sw1.add_edge(sw2)
                # Storing created link
                links.append((pair[0], pair[1]))
                links.append((pair[1], pair[0]))
                # Decreasing number of open ports on both switches
                open_ports[pair[0]] -= 1
                open_ports[pair[1]] -= 1
                # If on sw1/sw2 we run out of ports we decrease number of switch_left to be connected
                if open_ports[pair[0]] == 0:
                    switch_left -= 1
                if open_ports[pair[1]] == 0:
                    switch_left -= 1
                # Removing pair from list, switches already connected or do not have open ports
                switch_idx_pairs.remove(pair)
            else:
                switch_idx_pairs.remove(pair)

        # after connecting random pairs of switches there still might be switches not utilized (having more than 1
        # open port)
        while self.not_utilized_switches_exists(open_ports, num_switches):
            for idx, switch3 in enumerate(switches):
                if open_ports[idx] > 1:
                    pair_idx_1 = idx
                    pair_idx_2 = idx
                    old_edge = None
                    # we look for a pair of switches that are is connected but is not our neighbour (like in the paper)
                    while pair_idx_1 == idx or pair_idx_2 == idx or (idx, pair_idx_1) in links or (
                            idx, pair_idx_2) in links or old_edge is None:
                        pair = random.choice(links)
                        pair_idx_1 = pair[0]
                        pair_idx_2 = pair[1]
                        sw1 = switches[pair_idx_1]
                        sw2 = switches[pair_idx_2]
                        old_edge = sw1.find_edge(sw2)
                    # we found a pair, so as in the paper we remove the pair's link and connect to those switches
                    sw1.remove_edge(old_edge)
                    sw2.remove_edge(old_edge)
                    links.remove((pair_idx_1, pair_idx_2))
                    links.remove((pair_idx_2, pair_idx_1))

                    sw1.add_edge(switch3)
                    sw2.add_edge(switch3)
                    links.append((pair_idx_1, idx))
                    links.append((idx, pair_idx_1))
                    links.append((pair_idx_2, idx))
                    links.append((idx, pair_idx_2))
                    # so we utilized 2 ports on our switch
                    open_ports[idx] -= 2

        self.servers.extend(servers)
        self.switches.extend(switches)

    @staticmethod
    def not_utilized_switches_exists(open_ports, num_switches):
        # simply iterate open_ports list and stop when not utilized switch found
        for idx in range(num_switches):
            if open_ports[idx] > 1:
                return True
        return False

    # method for plotting the jellyfish topology
    def plot(self, save=False, mode=1):
        # scaling figure depending num_ports
        scale = 5 if self.num_ports > 6 else 3
        fig, ax = plt.subplots(figsize=(self.num_ports * scale, self.num_ports * scale))

        # Plotting servers, radius - we plot servers and switches on the circle
        r = 0.45
        server_ans = []
        if mode == 1:
            # choosing nodes separation in radians
            alfa_base = alfa_scale = 2 * math.pi / len(self.servers)
        else:
            alfa_base = alfa_scale = 2 * math.pi / (max(len(self.servers), len(self.switches)))
        for server in self.servers:
            an = ax.annotate(server.id, xy=(r * math.cos(alfa_scale) + 0.5, r * math.sin(alfa_scale) + 0.5),
                             bbox=dict(boxstyle="round", fc="w", color='red'))
            alfa_scale = alfa_scale + alfa_base
            server_ans.append(an)

        # plotting switches on the inner circe, lesser radius
        r = 0.35
        switch_ans = []
        if mode == 1:
            alfa_base = alfa_scale = 2 * math.pi / len(self.switches)
        else:
            alfa_base = alfa_scale = 2 * math.pi / (max(len(self.servers), len(self.switches)))
        for switch in self.switches:
            an = ax.annotate(switch.id, xy=(r * math.cos(alfa_scale) + 0.5, r * math.sin(alfa_scale) + 0.5),
                             bbox=dict(boxstyle="round", fc="w"))
            alfa_scale = alfa_scale + alfa_base
            switch_ans.append(an)

        # now we plot edges, first from hosts to switches
        plotted_edges = []
        for server in self.servers:
            for edge in server.edges:
                switch = edge.rnode
                server_idx = self.servers.index(server)
                switch_idx = self.switches.index(switch)
                server_an = server_ans[server_idx]
                switch_an = switch_ans[switch_idx]
                an = ax.annotate('', xy=(server_an.xy[0], server_an.xy[1]),
                                 xytext=(switch_an.xy[0], switch_an.xy[1]),
                                 arrowprops=dict(arrowstyle='-'))
                plotted_edges.append(edge)

        # now we plot edges between switches
        for switch in self.switches:
            for edge in switch.edges:
                if edge not in plotted_edges:
                    switch2 = edge.rnode
                    switch_idx = self.switches.index(switch)
                    switch2_idx = self.switches.index(switch2)
                    sw1_an = switch_ans[switch_idx]
                    sw2_an = switch_ans[switch2_idx]
                    an = ax.annotate('', xy=(sw1_an.xy[0], sw1_an.xy[1]),
                                     xytext=(sw2_an.xy[0], sw2_an.xy[1]),
                                     arrowprops=dict(arrowstyle='-'))
                    plotted_edges.append(edge)

        # either save the plot or jus display
        if save:
            plt.savefig('fig_jellyfish_k' + str(self.num_ports) + '.png')
        else:
            plt.show()
        plt.clf()
        fig.clf()


# endregion

# region Fattree
class Fattree:

    def __init__(self, num_ports):
        self.servers = []
        self.switches = []
        self.num_ports = num_ports
        self.generate()

    # function creating fattree topology
    def generate(self):
        dpid_maker = 1

        # We start with core layer switches
        core_layer_switches = []
        for i in range(1, int(self.num_ports / 2 + 1)):
            for j in range(1, int(self.num_ports / 2 + 1)):
                core_switch = Node(self.get_core_switch_id(i, j, self.num_ports), 'c_sw', 's' + str(dpid_maker))
                core_layer_switches.append(core_switch)
                dpid_maker = dpid_maker + 1

        # in each pod we separate adding lower layer switches with hosts and upper layer switches
        for pod_num in range(self.num_ports):
            lower_layer_switches = []
            upper_layer_switches = []

            # creation of lower layer switches
            for i in range(int(self.num_ports / 2)):
                switch = Node(self.get_pod_switch_id(pod_num, i), 'p_sw', 's' + str(dpid_maker))
                lower_layer_switches.append(switch)
                dpid_maker = dpid_maker + 1

            # for each lower layer switch we create the hosts and connect them
            for i, switch in enumerate(lower_layer_switches):
                for j in range(2, int(self.num_ports / 2 + 2)):
                    host = Node(self.get_host_id(pod_num, i, j), 'h')
                    host.add_edge(switch)
                    self.servers.append(host)

            # creating upper layer switches
            for i in range(int(self.num_ports / 2), self.num_ports):
                switch = Node(self.get_pod_switch_id(pod_num, i), 'p_sw', 's' + str(dpid_maker))
                upper_layer_switches.append(switch)
                dpid_maker = dpid_maker + 1

            # connecting upper layer switches with core layer switches
            for i in range(int((self.num_ports / 2) ** 2)):
                # we calculate stride_num which indicate to which upper layer switch we connect the core switch
                # stride_num is based on floor division - property of addressing in fattree
                stride_num = int(i // (self.num_ports / 2))
                core_layer_switches[i].add_edge(upper_layer_switches[stride_num])

            # connecting switches in pod
            for lower in lower_layer_switches:
                for upper in upper_layer_switches:
                    lower.add_edge(upper)

            self.switches.extend(lower_layer_switches)
            self.switches.extend(upper_layer_switches)

        self.switches.extend(core_layer_switches)

    # 3 utility functions for proper addressing of the nodes
    @staticmethod
    def get_pod_switch_id(pod_num, switch_num):
        return '10.' + str(pod_num) + '.' + str(switch_num) + '.1'

    @staticmethod
    def get_core_switch_id(core_x, core_y, num_ports):
        return '10.' + str(num_ports) + '.' + str(core_x) + '.' + str(core_y)

    @staticmethod
    def get_host_id(pod_num, switch_num, host_num):
        return '10.' + str(pod_num) + '.' + str(switch_num) + '.' + str(host_num)

    # func for plotting fattree topo
    def plot(self, save=False):
        # scaling the plot based on num_ports
        scale = 5 if self.num_ports > 6 else 3
        fig, ax = plt.subplots(figsize=(self.num_ports * scale * 2, self.num_ports * scale))

        # plotting servers first
        server_ans = []
        # setting separation of nodes on the plot (bottom of teh plot)
        x_base = x_scale = 1 / (len(self.servers) + 1)
        for server in self.servers:
            an = ax.annotate(server.id, xy=(0.0 + x_scale, 0.05), bbox=dict(boxstyle="round", fc="w", color='red'),
                             rotation=90)
            x_scale = x_scale + x_base
            server_ans.append(an)

        # plotting core switches (top of the plot)
        core_ans = []
        core_switches = [switch for switch in self.switches if switch.type == 'c_sw']
        x_base = x_scale = 1 / (len(core_switches) + 1)
        for switch in core_switches:
            an = ax.annotate(switch.id, xy=(0.0 + x_scale, 0.95), bbox=dict(boxstyle="round", fc="w"))
            x_scale = x_scale + x_base
            core_ans.append(an)

        lower_pod_ans = []
        upper_pod_ans = []
        # selecting pod switches from all switches to simplify plotting
        pod_switches = [switch for switch in self.switches if switch.type == 'p_sw']
        # list of values used to filter lower/upper pod switches - based on num_ports
        modulo_values = [n for n in range(int(self.num_ports / 2))]
        # 2 lists, of lower and upper pod switches
        lower_pod_switches = [switch for idx, switch in enumerate(pod_switches) if
                              idx % self.num_ports in modulo_values]
        upper_pod_switches = [switch for switch in pod_switches if switch not in lower_pod_switches]
        x_base = x_scale = 1 / (len(lower_pod_switches) + 1)

        # plotting lower layer
        for switch in lower_pod_switches:
            an = ax.annotate(switch.id, xy=(0.0 + x_scale, 0.4), bbox=dict(boxstyle="round", fc="w"))
            x_scale = x_scale + x_base
            lower_pod_ans.append(an)

        # plotting upper layer
        x_scale = x_base
        for switch in upper_pod_switches:
            an = ax.annotate(switch.id, xy=(0.0 + x_scale, 0.6), bbox=dict(boxstyle="round", fc="w"))
            x_scale = x_scale + x_base
            upper_pod_ans.append(an)

        # plotting edges between hosts and lower layer switches
        plotted_edges = []
        for server in self.servers:
            for edge in server.edges:
                switch = edge.rnode
                server_idx = self.servers.index(server)
                switch_idx = lower_pod_switches.index(switch)
                # we use stored annotations plotted to use their location for plotting edges
                server_an = server_ans[server_idx]
                switch_an = lower_pod_ans[switch_idx]
                an = ax.annotate('', xy=(server_an.xy[0], server_an.xy[1]),
                                 xytext=(switch_an.xy[0], switch_an.xy[1]),
                                 arrowprops=dict(arrowstyle='-'))
                plotted_edges.append(edge)

        # plotting edges between core switches and upper layer switches
        for core_switch in core_switches:
            for edge in core_switch.edges:
                pod_switch = edge.rnode
                core_switch_idx = core_switches.index(core_switch)
                pod_switch_idx = upper_pod_switches.index(pod_switch)
                core_an = core_ans[core_switch_idx]
                pod_an = upper_pod_ans[pod_switch_idx]
                an = ax.annotate('', xy=(core_an.xy[0], core_an.xy[1]),
                                 xytext=(pod_an.xy[0], pod_an.xy[1]),
                                 arrowprops=dict(arrowstyle='-'))
                plotted_edges.append(edge)

        # plotting edges between switches in pods
        for upper_switch in upper_pod_switches:
            for edge in upper_switch.edges:
                if edge not in plotted_edges:
                    lower_switch = edge.lnode
                    upper_switch_idx = upper_pod_switches.index(upper_switch)
                    lower_switch_idx = lower_pod_switches.index(lower_switch)
                    upper_an = upper_pod_ans[upper_switch_idx]
                    lower_an = lower_pod_ans[lower_switch_idx]
                    an = ax.annotate('', xy=(upper_an.xy[0], upper_an.xy[1]),
                                     xytext=(lower_an.xy[0], lower_an.xy[1]),
                                     arrowprops=dict(arrowstyle='-'))
                    plotted_edges.append(edge)

        if save:
            plt.savefig('fig_fattree_k' + str(self.num_ports) + '.png')
        else:
            plt.show()
        plt.clf()
        fig.clf()


# endregion

# region Prioritize

# utility class used for priority queue, in python3.x it is not possible to use priority queue
# with not comparable items and not unique priority values
class Prioritize(object):
    def __init__(self, priority, object):
        self.priority = priority
        self.object = object

    # our own comparator function
    def __lt__(self, other):
        return self.priority < other.priority


# endregion

# region Dijkstra

# implementation of dijkstra algorithm, from starting node to every other in graph
def dijkstra(start_vertex, vertices):
    # sets for saving the results
    # result - for costs of paths to each node
    # previous - for previous step - used later for reproducing paths
    result = {}
    previous = {}

    # we start with setting distance to each node as 'infinity'
    for switch in vertices:
        result[switch] = float('inf')
    # distance to where we are is 0
    result[start_vertex] = 0
    # list to store already visited nodes
    visited = []

    # we initialize the priority queue, used to put possible paths from current node
    p_queue = queue.PriorityQueue()
    p_queue.put(Prioritize(0, start_vertex))

    # we run the algorith until we vae possible move (node in the queue)
    while not p_queue.empty():
        # we get next hop from queue and mark it as visited
        current_vertex = p_queue.get().object
        visited.append(current_vertex)

        for neighbor in vertices:
            if current_vertex.is_neighbor(neighbor):
                # we do not have weights (or path bandwidth) so we set 1 as cost of reaching next hop
                distance = 1
                # for each of reachable nodes, if one hasn't been visited yet we go there
                if neighbor not in visited:
                    old_cost = result[neighbor]
                    new_cost = result[current_vertex] + distance
                    # if we have reached the node cheaper than before - save the path
                    if new_cost < old_cost:
                        p_queue.put(Prioritize(new_cost, neighbor))
                        result[neighbor] = new_cost
                        previous[neighbor] = current_vertex
    return result, previous


# utility function for printing the shortest path calculated in dijkstra algorithm
def print_path(previous, start_node, end_node):
    node = end_node
    path = []
    while node != start_node:
        path.append(node)
        node = previous[node]

    path.append(start_node)
    # we traversed the path backwards, so reverse the list
    path.reverse()

    print(start_node.type + str(start_node.id), end='')
    for i in range(1, len(path)):
        print(' -> ' + path[i].type + str(path[i].id), end='')
    print('')


# utility function for getting the path between two nodes, based on previous list from dijkstra algorithm
def get_path(previous, start_node, end_node):
    node = end_node
    path = []
    while node != start_node:
        path.append(node)
        node = previous[node]

    path.append(start_node)
    # we traversed the path backwards, so reverse the list
    path.reverse()
    return path


def get_path_dpid(previous, start_node, end_node):
    node = end_node
    path = []
    while node != start_node:
        path.append(get_dpid_from_str(node))
        node = previous[node]

    path.append(get_dpid_from_str(node))
    # we traversed the path backwards, so reverse the list
    path.reverse()
    return path

def get_dpid_from_str(node):
    if node.dpid is not None:
         return int(node.dpid[1:])
    else:
        return node.id


# utility function for getting the path between two nodes, it executes the dijkstra algorithm
def dijkstra_get_path(start_vertex, end_node, vertices):
    distance, previous = dijkstra(start_vertex, vertices)

    # it is possible that path between two nodes does not exist!
    if distance[end_node] == float('inf'):
        return distance[end_node], []

    node = end_node
    path = []
    while node != start_vertex:
        path.append(node)
        node = previous[node]

    path.append(start_vertex)
    # we traversed the path backwards, so reverse the list
    path.reverse()
    return distance[end_node], path


# endregion

# region Yen
def ksp_yen(vertices, node_start, node_end, max_k):
    distances, previous = dijkstra(node_start, vertices)

    # Shortest path from the source to the target
    A = [{'cost': distances[node_end],
          'path': get_path(previous, node_start, node_end)}]
    # Initialize the heap to store the potential k-th shortest path
    B = queue.PriorityQueue()

    if not A[0]['path']:
        return A

    for _ in range(1, max_k):
        # The spur node ranges from the first node to the next to last node in the shortest path
        for i in range(0, len(A[-1]['path']) - 1):
            # Spur node is retrieved from the previous k-shortest path
            node_spur = A[-1]['path'][i]
            # The sequence of nodes from the source to the spur node of the previous k-shortest path
            path_root = A[-1]['path'][:i + 1]

            # We store the removed edges
            edges_removed = []
            for path_k in A:
                curr_path = path_k['path']
                if len(curr_path) > i and path_root == curr_path[:i + 1]:
                    # Remove the links that are part of the previous shortest paths which share the same root path
                    edge = curr_path[i].find_edge(curr_path[i + 1])
                    curr_path[i].remove_edge(edge)
                    curr_path[i + 1].remove_edge(edge)
                    edges_removed.append([curr_path[i], curr_path[i + 1], 1])

                # Calculate the spur path from the spur node to the sink
            _, path_spur = dijkstra_get_path(node_spur, node_end, vertices)

            if path_spur:
                # Entire path is made up of the root path and spur path
                path_total = path_root[:-1] + path_spur
                dist_total = path_cost(_, path_total)
                potential_k = {'cost': dist_total, 'path': path_total}
                # Add the potential k-shortest path to the heap
                B.put(Prioritize(potential_k['cost'], potential_k))

            # Add back the edges that were removed from the graph
            for edge in edges_removed:
                edge[0].add_edge(edge[1])
                edge[1].add_edge(edge[0])

            # The lowest cost path becomes the k-shortest path.
        while True and not B.empty():
            path_ = B.get().object
            if path_ not in A:
                # We found a new path to add
                A.append(path_)
                break
    return A


def path_cost(_, path):
    cost_of_path = 0
    for i in range(len(path)):
        if i > 0:
            # just count the number of edges
            cost_of_path += 1
    return cost_of_path

# endregion
