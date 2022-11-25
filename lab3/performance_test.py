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
    return ret / len(result)


def get_avg_rtt(ping_output):
    return re.search("rtt min/avg/max/mdev = (\d+.\d+)/(\d+.\d+)/(\d+.\d+)/(\d+.\d+)", str(ping_output)).group(2)


def performanceTest(net):
    h0, h1, h2, h4 = net.get('host0', 'host1', 'host2', 'host4')
    time = 20

    print(h0.IP())
    print(h1.IP())

    print("Testing throughput")
    perf1 = get_mean(net.iperf((h0, h1), seconds=time))
    perf2 = get_mean(net.iperf((h0, h2), seconds=time))
    perf3 = get_mean(net.iperf((h0, h4), seconds=time))
    result1 = [perf1, perf2, perf3]

    print("Testing latency")
    ping1 = h0.cmd('ping', '-c20', h1.IP())
    ping2 = h0.cmd('ping', '-c20', h2.IP())
    ping3 = h0.cmd('ping', '-c20', h4.IP())
    result2 = [get_avg_rtt(ping1), get_avg_rtt(ping2), get_avg_rtt(ping3)]

    controller = "ft"  # change
    ylabel1 = "Throughput in GBits/sec"
    ylabel2 = "AVG RTT in ms"
    x = [1, 2, 3]
    labels = ["Scenario 1", "Scenario 2", "Scenario 3"]

    f1 = plt.figure()
    plt.bar(x, result1)
    plt.xticks(x, labels)
    plt.ylabel(ylabel1)
    plt.savefig('fig_throughput_' + str(controller) + '.png')

    plt.clf()

    f2 = plt.figure()
    plt.bar(x, result2)
    plt.xticks(x, labels)
    plt.ylabel(ylabel2)
    plt.savefig('fig_rtt_' + str(controller) + '.png')


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