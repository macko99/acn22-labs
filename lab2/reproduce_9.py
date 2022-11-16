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
import operator
import matplotlib.pyplot as plt
import copy
import sys
from multiprocessing import Manager
import multiprocessing as mp
from tqdm import tqdm

sys.setrecursionlimit(10000)
progress_bar = None


# # Setup for Jellyfish
# num_servers = 686
# num_switches = 245
# num_ports = 14

# jf_topo = topo.Jellyfish(num_servers, num_switches, num_ports)

# TODO: code for reproducing Figure 9 in the jellyfish paper

# function to get exactly k number of the shortest paths
def get_k_shortest_paths(array, k):
    result = []
    for x in range(min(k, len(array))):
        result.append(array[x]['path'])
    return result


# function to get exactly k paths that are not longer than the shortest one
def get_shortest_paths_max_k(array, k):
    result = []
    threshold = array[0]['cost']
    for x in range(min(k, len(array))):
        if array[x]['cost'] != threshold:
            return result
        result.append(array[x]['path'])
    return result


# function to count paths that are on each link
def count_paths(array):
    counter = {}
    for route in array:
        for x in range(len(route) - 1):
            if hash_nodes(route[x], route[x + 1]) in counter.keys():
                # if path goes through the link - we increase the counter
                counter[hash_nodes(route[x], route[x + 1])] += 1
            else:
                counter[hash_nodes(route[x], route[x + 1])] = 1
    return counter


# this function prepares set to be plotted
# we sort the set with all links and corresponding number of paths on this link
# than we match it with incremental rank of the link
def prepare_data_for_plotting(array):
    sorted_array = sorted(array.items(), key=operator.itemgetter(1))
    result_set = [[0], [0]]
    last_rank = 0
    last_value = 0
    result_set[0].append(last_rank)
    result_set[1].append(last_value)
    for item in sorted_array:
        # for each link we increase the rank
        last_rank += 1
        # if there is change in number of paths link is on we store new values to teh result set
        if last_value != item[1]:
            result_set[0].append(last_rank)
            result_set[1].append(last_value)
            last_value = item[1]
    return result_set


# utility function to hash each link - we use string consisting of corresponding node's ids
def hash_nodes(node1, node2):
    return str(node1.type) + str(node1.id) + ':' + str(node2.type) + str(node2.id)


# function that is executed in each process
def thread_wrapper(res_k8, res_e8, res_e64, graph, pair_th):
    # we run Yen's algorithm for two switches
    part_result = topo.ksp_yen(graph, pair_th[0], pair_th[1], 16)
    # and we merge the results, respecting 3 separate sets for each routing method
    res_k8.extend(get_k_shortest_paths(part_result, 8))
    res_e8.extend(get_shortest_paths_max_k(part_result, 8))
    res_e64.extend(get_shortest_paths_max_k(part_result, 16))


# utility function used for reporting process to the progress bar displayed to the user
def update(*a):
    progress_bar.update()


if __name__ == "__main__":
    # our setup for the figure 9, just like in the paper
    num_ports = 14
    num_servers = int((num_ports ** 3) / 4)
    num_switches = int(num_ports * num_ports * 5 / 4)

    # multiprocessing safe lists
    manager = Manager()
    set_k8 = manager.list()
    set_e8 = manager.list()
    set_e64 = manager.list()

    # initializing the jellyfish topology
    jf_topo = topo.Jellyfish(num_servers, num_switches, num_ports)

    # pool of workers (processes), number depends on the CPU (no of cores)
    pool = mp.Pool(mp.cpu_count())
    progress_bar = tqdm(total=1000)

    # since the connections are random, we will perform 1000 iterations of Yen's algorithm
    # # (paths between two random switches)
    for idx in range(1000):
        # we copy our topo into each process (needed because Yen's implementation is removing nodes from graph)
        # if you run this on Windows, you should change it to copy.copy()
        data = copy.deepcopy(jf_topo)
        jf_switches_links = [(a, b) for idx, a in enumerate(data.switches) for b in data.switches[idx + 1:]]
        # we choose random pair of switches and register new worker process
        pair = jf_switches_links[idx]
        pool.apply_async(thread_wrapper, args=(set_k8, set_e8, set_e64, data.switches, pair), callback=update)

    # we close the pool and wait for all processes to finish its work
    pool.close()
    pool.join()

    # we process the results and preparing them for plotting
    set_k8 = count_paths(set_k8)
    set_e8 = count_paths(set_e8)
    set_e64 = count_paths(set_e64)

    set_k8 = prepare_data_for_plotting(set_k8)
    set_e8 = prepare_data_for_plotting(set_e8)
    set_e64 = prepare_data_for_plotting(set_e64)

    # plotting the figure 9
    plt.switch_backend('Agg')
    plt.step(set_k8[0], set_k8[1], label='8 Shortest Paths')
    plt.step(set_e64[0], set_e64[1], label='64-way ECMP', linestyle=':')
    plt.step(set_e8[0], set_e8[1], label='8-way ECMP', linestyle=':')
    plt.ylim([0, 18])
    plt.xlim([0, 3000])
    plt.legend()
    plt.xlabel("Rank of Link")
    plt.ylabel("# Distinct Paths link is on")
    plt.savefig('figure_9.png')
    plt.close()
    plt.clf()
