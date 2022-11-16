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
import time


count_ksp = {}
count_ecmp8 = {}
count_ecmp64 = {}

def handleKSP(paths, ksp_value):
    for path in paths[:ksp_value]:
        #links = [(min(x.id, y.id), max(x.id, y.id)) for x, y in zip(path ,path[1::])]
        links = [(x.id, y.id) for x, y in zip(path ,path[1::])]
        for link in links:
            try:
                count_ksp[link] += 1
            except KeyError:
                count_ksp[(link[1], link[0])] += 1


def handleECMP8way(paths):
    len_shortest = len(paths[0])
    ecmp_val = 8
    for path in paths:
        if len(path) == len_shortest:
            if ecmp_val >= 0:
                #links = [(min(x.id, y.id), max(x.id, y.id)) for x, y in zip(path ,path[1::])]
                links = [(x.id, y.id) for x, y in zip(path ,path[1::])]
                for link in links:
                    try:
                        count_ecmp8[link] += 1
                    except KeyError:
                        count_ecmp8[(link[1], link[0])] += 1
                    ecmp_val -= 1


def handleECMP64way(paths):
    len_shortest = len(paths[0])
    ecmp_val = 64
    for path in paths:
        if len(path) == len_shortest:
            if ecmp_val >= 0:
                #links = [(min(x.id, y.id), max(x.id, y.id)) for x, y in zip(path ,path[1::])]
                links = [(x.id, y.id) for x, y in zip(path ,path[1::])]
                for link in links:
                    try:
                        count_ecmp64[link] += 1
                    except KeyError:
                        count_ecmp64[(link[1], link[0])] += 1
                    ecmp_val -= 1



def init_counters(links):
    for link in links:
        count_ksp[link] = 0
        count_ecmp8[link] = 0
        count_ecmp64[link] = 0


if __name__ == "__main__":

    start = time.time()

    num_ports = 4
    num_servers = int((num_ports ** 3) / 4)
    num_switches = int(num_ports * num_ports * 5 / 4)

    jf_topo = topo.Jellyfish(num_servers, num_switches, num_ports)
    switches_pairs = [(a, b) for idx, a in enumerate(jf_topo.switches) for b in jf_topo.switches[idx + 1:]]

    edges = set()

    for switch in jf_topo.switches:
        for edge in switch.edges:
            if edge.lnode.id == edge.rnode.id:
                continue
            edges.add((edge.lnode.id, edge.rnode.id))
    
    init_counters(edges)
    print(count_ksp)
    
    for pair in switches_pairs:
        print("Pair" + str(pair[0].id) + "/" + str(pair[1].id))
        result = topo.ksp_yen(jf_topo.switches + jf_topo.servers, pair[0], pair[1], 8)
        paths = [route["path"] for route in result]
        for route in result:
            print(str(route['cost']) + ': ', end='')
            for node in route['path']:
                print(str(node.type) + str(node.id) + ' -> ', end='')
            print('')
        handleKSP(paths, 8)
        handleECMP8way(paths)
        handleECMP64way(paths)


    #add plot for reproducing figure 9
    plt.ylabel('# Distinct Paths Link is on')
    plt.xlabel('Rank of Link')

    plt.plot(sorted(count_ecmp64.values()), color='red', label='64-way ECMP')
    plt.plot(sorted(count_ksp.values()), color='blue', label="8 Shortest Paths")
    plt.plot(sorted(count_ecmp8.values()), color='green', label='8-way ECMP')


    plt.legend()
    #plt.show()
    plt.savefig("fig_9.png")
    plt.close()

    print(time.time() - start)
