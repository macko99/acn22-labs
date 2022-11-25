from mininet.net import Mininet
import matplotlib.pyplot as plt
from mininet.node import RemoteController
from mininet.log import setLogLevel
from fat_tree import FattreeNet
from topo import Fattree
import re

def get_mean(result):
    ret = 0
    for res in result:
        ret += int(re.search(r'\d+', res).group())
    return ret/len(result)

def plot_fig(values, controller, ylabel):
    x = [1,2,3]
    labels = ["Scenario 1", "Scenario 2", "Scenario 3"]
    plt.bar(x, values)
    plt.xticks(x, labels)
    plt.ylabel(ylabel)
    plt.savefig('fig_throughput_' + str(controller) + '.png')


def performanceTest(net):
    h0, h1, h2, h4 = net.get('host0', 'host1', 'host2', 'host4')
    print("Testing throughput")
    time = 20
    perf1 = get_mean(net.iperf((h0, h1), seconds=time))
    perf2 = get_mean(net.iperf((h0, h2), seconds=time))
    perf3 = get_mean(net.iperf((h0, h4), seconds=time))
    result1 = [perf1, perf2, perf3]

    controller = "sp" #change

    plot_fig(result1, controller, "Throughput in GBits/sec")

    
if __name__ == "__main__":
    setLogLevel('info')
    num_ports = 4
    ft_topo = Fattree(num_ports)
    ft_net = FattreeNet(ft_topo)
    net = Mininet(ft_net, controller=None)
    net.addController('c0', controller=RemoteController, ip="127.0.0.1", port=6633)
    net.start()

    performanceTest(net)

    net.stop()