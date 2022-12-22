from lib import config # do not import anything before this
from p4app import P4Mininet
from mininet.topo import Topo
from mininet.cli import CLI
import os

NUM_WORKERS = 3

class SMLTopo(Topo):
    def __init__(self, **opts):
        Topo.__init__(self, **opts)

        s0 = self.addSwitch('s0', ip='10.0.2.15/24')
        for rank in range(NUM_WORKERS):
            worker = self.addHost('w' + str(rank), ip='10.0.2.' + str(rank) + '/24')
            self.addLink(worker, s0, bw=15, delay='1ms', port1=1)

def RunWorkers(net):
    """
    Starts the workers and waits for their completion.
    Redirects output to logs/<worker_name>.log (see lib/worker.py, Log())
    This function assumes worker i is named 'w<i>'. Feel free to modify it
    if your naming scheme is different
    """
    worker = lambda rank: "w%i" % rank
    log_file = lambda rank: os.path.join(os.environ['APP_LOGS'], "%s.log" % worker(rank))
    for i in range(NUM_WORKERS):
        net.get(worker(i)).sendCmd('python worker.py %d > %s' % (i, log_file(i)))
    for i in range(NUM_WORKERS):
        net.get(worker(i)).waitOutput()

def RunControlPlane(net):
    """
    One-time control plane configuration
    """
    s0 = net.get("s0")
    s0.addMulticastGroup(mgid=1, ports=range(1, NUM_WORKERS + 1))
    s0.setMAC("00:00:00:00:00:ff")
    for i in range(NUM_WORKERS):
        net.get("w" + str(i)).setARP('10.0.2.15', "00:00:00:00:00:ff")

topo = SMLTopo()
net = P4Mininet(program="p4/main.p4", topo=topo)
net.run_control_plane = lambda: RunControlPlane(net)
net.run_workers = lambda: RunWorkers(net)
net.start()
net.run_control_plane()
CLI(net)
net.stop()
