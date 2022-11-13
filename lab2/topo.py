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

import sys
import random
import matplotlib.pyplot as plt
import math

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

# Class for a node in the graph
class Node:
	def __init__(self, id, type):
		self.edges = []
		self.id = id
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


class Jellyfish:

	def __init__(self, num_servers, num_switches, num_ports, plot=False, save=False, mode=1):
		self.servers = []
		self.switches = []
		self.generate(num_servers, num_switches, num_ports)
		if plot:
			self.plot(num_ports, save, mode)

	def generate(self, num_servers, num_switches, num_ports):
		
		switches = []
		open_ports = []
		for i in range(num_switches):
			switch = Node(i, 'sw')
			switches.append(switch)
			open_ports.append(num_ports)

		servers = []
		for i in range(num_servers):
			host = Node(i, 'h')
			switch = switches[i%num_switches]
			host.add_edge(switch)
			open_ports[i%num_switches] -= 1
			servers.append(host)

		links = []
		switch_idx_list = [n for n in range(num_switches)] 
		switch_idx_pairs = [(a, b) for idx, a in enumerate(switch_idx_list) for b in switch_idx_list[idx + 1:]]
		switch_left = num_switches

		while switch_left > 1 and switch_idx_pairs:
			pair = random.choice(switch_idx_pairs)
			if open_ports[pair[0]] > 0 and open_ports[pair[1]] > 0:
				sw1 = switches[pair[0]]
				sw2 = switches[pair[1]]
				sw1.add_edge(sw2)
				links.append((pair[0], pair[1]))
				links.append((pair[1], pair[0]))
				open_ports[pair[0]] -= 1
				open_ports[pair[1]] -= 1
				if open_ports[pair[0]] == 0:
					switch_left -=1
				if open_ports[pair[1]] == 0:
					switch_left -=1
				switch_idx_pairs.remove(pair)
			else:
				switch_idx_pairs.remove(pair)

		while self.not_utilized_switches_exists(open_ports, num_switches):
			for idx, switch3 in enumerate(switches):
				if open_ports[idx] > 1:
					pair_idx_1 = idx
					pair_idx_2 = idx
					old_edge = None
					while pair_idx_1 == idx or pair_idx_2 == idx or (idx, pair_idx_1) in links or (idx, pair_idx_2) in links or old_edge == None:
						pair = random.choice(links)
						pair_idx_1 = pair[0]
						pair_idx_2 = pair[1]
						sw1 = switches[pair_idx_1]
						sw2 = switches[pair_idx_2]
						old_edge = self.find_edge(sw1, sw2)
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
					open_ports[idx] -= 2

		self.servers.extend(servers)
		self.switches.extend(switches)
		

	def find_edge(self, node1, node2):
		for edge in node1.edges:
			if edge.lnode == node2 or edge.rnode == node2:
				return edge
		return None

	def not_utilized_switches_exists(self, open_ports, num_switches):
		for idx in range(num_switches):
			if open_ports[idx] > 1:
				return True
		return False

	def plot(self, num_ports, save, mode):
		scale = 5 if num_ports > 6 else 3
		fig, ax = plt.subplots(figsize=(num_ports*scale, num_ports*scale))
		
		r = 0.45
		server_ans = []
		if mode == 1:
			alfa_base = alfa_scale = 2*math.pi/len(self.servers)
		else:
			alfa_base = alfa_scale = 2*math.pi/(max(len(self.servers), len(self.switches)))
		for server in self.servers:
			an = ax.annotate(server.id, xy=(r*math.cos(alfa_scale)+0.5, r*math.sin(alfa_scale)+0.5), bbox=dict(boxstyle="round", fc="w", color='red'))
			alfa_scale = alfa_scale + alfa_base
			server_ans.append(an)

		r = 0.35
		switch_ans = []
		if mode == 1:
			alfa_base = alfa_scale = 2*math.pi/len(self.switches)
		else:
			alfa_base = alfa_scale = 2*math.pi/(max(len(self.servers), len(self.switches)))
		for switch in self.switches:
			an = ax.annotate(switch.id, xy=(r*math.cos(alfa_scale)+0.5, r*math.sin(alfa_scale)+0.5), bbox=dict(boxstyle="round", fc="w"))
			alfa_scale = alfa_scale + alfa_base
			switch_ans.append(an)

		ploted_edges = []
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
				ploted_edges.append(edge)

		for switch in self.switches:
			for edge in switch.edges:
				if edge not in ploted_edges:
					switch2 = edge.rnode
					switch_idx = self.switches.index(switch)
					switch2_idx = self.switches.index(switch2)
					sw1_an = switch_ans[switch_idx]
					sw2_an = switch_ans[switch2_idx]
					an = ax.annotate('', xy=(sw1_an.xy[0], sw1_an.xy[1]), 
									 xytext=(sw2_an.xy[0], sw2_an.xy[1]), 
									 arrowprops=dict(arrowstyle='-'))
					ploted_edges.append(edge)
		
		if save:
			plt.savefig('fig_jellyfish_k' + str(num_ports) + '.png')
		else:
			plt.show()
		plt.clf()
		fig.clf()

		

class Fattree:

	def __init__(self, num_ports, plot=False, save=False):
		self.servers = []
		self.switches = []
		self.generate(num_ports)
		if plot:
			self.plot(num_ports, save)

	def generate(self, num_ports):

		core_layer_switches = []
		for i in range(1, int(num_ports/2 + 1)):
			for j in range(1, int(num_ports/2 + 1)):
				core_switch = Node(self.get_core_switch_id(i, j, num_ports), 'c_sw')
				core_layer_switches.append(core_switch)

		for pod_num in range(num_ports):
			lower_layer_switches = []
			upper_layer_switches = []

			for i in range(int(num_ports/2)):
				switch = Node(self.get_pod_switch_id(pod_num, i), 'p_sw')
				lower_layer_switches.append(switch)

			for i, switch in enumerate(lower_layer_switches):
				for j in range(2, int(num_ports/2 + 2)):
					host = Node(self.get_host_id(pod_num, i, j), 'h')
					host.add_edge(switch)
					self.servers.append(host)

			for i in range(int(num_ports/2), num_ports):
				switch = Node(self.get_pod_switch_id(pod_num, i), 'p_sw')
				upper_layer_switches.append(switch)

			for i in range(int((num_ports/2)**2)):
				stride_num = int(i // (num_ports/2))
				core_layer_switches[i].add_edge(upper_layer_switches[stride_num])

			for lower in lower_layer_switches:
				for upper in upper_layer_switches:
					lower.add_edge(upper)
			
			self.switches.extend(lower_layer_switches)
			self.switches.extend(upper_layer_switches)

		self.switches.extend(core_layer_switches)


	def get_pod_switch_id(self, pod_num, switch_num):
		return '10.' + str(pod_num) + '.' + str(switch_num) + '.1'

	def get_core_switch_id(self, core_x, core_y, num_ports):
		return '10.' + str(num_ports) + '.' + str(core_x) + '.' + str(core_y)

	def get_host_id(self, pod_num, switch_num, host_num):
		return '10.' + str(pod_num) + '.' + str(switch_num) + '.' + str(host_num)



	def plot(self, num_ports, save):
		scale = 5 if num_ports > 6 else 3
		fig, ax = plt.subplots(figsize=(num_ports*scale*2, num_ports*scale))

		server_ans = []
		x_base = x_scale = 1/(len(self.servers)+1)
		for server in self.servers:
			an = ax.annotate(server.id, xy=(0.0+x_scale, 0.05), bbox=dict(boxstyle="round", fc="w", color='red'), rotation=90)
			x_scale = x_scale + x_base
			server_ans.append(an)

		core_ans = []
		core_switches = [switch for switch in self.switches if switch.type == 'c_sw']
		x_base = x_scale = 1/(len(core_switches)+1)
		for switch in core_switches:
			an = ax.annotate(switch.id, xy=(0.0+x_scale, 0.95), bbox=dict(boxstyle="round", fc="w"))
			x_scale = x_scale + x_base
			core_ans.append(an)

		lower_pod_ans = []
		upper_pod_ans = []
		pod_switches = [switch for switch in self.switches if switch.type == 'p_sw']
		modulo_values = [n for n in range(int(num_ports/2))]
		lower_pod_switches = [switch for idx, switch in enumerate(pod_switches) if idx%num_ports in modulo_values]
		upper_pod_switches = [switch for switch in pod_switches if switch not in lower_pod_switches]
		x_base = x_scale = 1/(len(lower_pod_switches) +1)

		for switch in lower_pod_switches:
			an = ax.annotate(switch.id, xy=(0.0+x_scale, 0.4), bbox=dict(boxstyle="round", fc="w"))
			x_scale = x_scale + x_base
			lower_pod_ans.append(an)

		x_scale = x_base
		for switch in upper_pod_switches:
			an = ax.annotate(switch.id, xy=(0.0+x_scale, 0.6), bbox=dict(boxstyle="round", fc="w"))
			x_scale = x_scale + x_base
			upper_pod_ans.append(an)

		ploted_edges = []
		for server in self.servers:
			for edge in server.edges:
				switch = edge.rnode
				server_idx = self.servers.index(server)
				switch_idx = lower_pod_switches.index(switch)
				server_an = server_ans[server_idx]
				switch_an = lower_pod_ans[switch_idx]
				an = ax.annotate('', xy=(server_an.xy[0], server_an.xy[1]), 
									 xytext=(switch_an.xy[0], switch_an.xy[1]), 
									 arrowprops=dict(arrowstyle='-'))
				ploted_edges.append(edge)

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
				ploted_edges.append(edge)

		for upper_switch in upper_pod_switches:
			for edge in upper_switch.edges:
				if edge not in ploted_edges:
					lower_switch = edge.lnode
					upper_switch_idx = upper_pod_switches.index(upper_switch)
					lower_switch_idx = lower_pod_switches.index(lower_switch)
					upper_an = upper_pod_ans[upper_switch_idx]
					lower_an = lower_pod_ans[lower_switch_idx]
					an = ax.annotate('', xy=(upper_an.xy[0], upper_an.xy[1]), 
									 	 xytext=(lower_an.xy[0], lower_an.xy[1]), 
									 	 arrowprops=dict(arrowstyle='-'))
					ploted_edges.append(edge)

		if save:
			plt.savefig('fig_fattree_k' + str(num_ports) + '.png')
		else:
			plt.show()
		plt.clf()
		fig.clf()
		
		