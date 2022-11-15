################################################################
##                                                            ##
##  script used for plotting the Fattree and Jellyfish topos  ##
##                                                            ##
################################################################
##                                                            ##
##  There is topo.plot(params) method available on each topo  ##
##                                                            ##
##  for fattree it support 1 parameter:                       ##
##      save - if True, plot will be saved as .png file       ##
##                                                            ##
##  for jellyfish it supports 2 parameters:                   ##
##      save - if True, plot will be saved as .png file       ##
##      mode - (1 or 2) changes nodes layout, for better look ##
##                                                            ##
################################################################

import topo

if __name__ == "__main__":
    # k - num_of_ports - as presented in lectures

    # _____________num_ports = 4___________________

    num_ports = 4
    num_servers = int((num_ports ** 3) / 4)
    num_switches = int(num_ports * num_ports * 5 / 4)

    fattree = topo.Fattree(num_ports)
    fattree.plot(save=True)

    jellyfish = topo.Jellyfish(num_servers, num_switches, num_ports)
    jellyfish.plot(save=True, mode=2)

    # # _____________num_ports = 6___________________

    # num_ports = 6
    # num_servers = int((num_ports ** 3) / 4)
    # num_switches = int(num_ports * num_ports * 5 / 4)
    #
    # fattree = topo.Fattree(num_ports)
    # fattree.plot(save=True)
    #
    # jellyfish = topo.Jellyfish(num_servers, num_switches, num_ports)
    # jellyfish.plot(save=True, mode=2)

    # _____________num_ports = 8___________________

    num_ports = 8
    num_servers = int((num_ports ** 3) / 4)
    num_switches = int(num_ports * num_ports * 5 / 4)

    fattree = topo.Fattree(num_ports)
    fattree.plot(save=True)

    jellyfish = topo.Jellyfish(num_servers, num_switches, num_ports)
    jellyfish.plot(save=True, mode=1)

    # _____________num_ports = 10___________________

    # num_ports = 10
    # num_servers = int((num_ports ** 3) / 4)
    # num_switches = int(num_ports * num_ports * 5 / 4)
    #
    # fattree = topo.Fattree(num_ports)
    # fattree.plot(save=True)
    #
    # jellyfish = topo.Jellyfish(num_servers, num_switches, num_ports)
    # jellyfish.plot(save=True, mode=1)

    # _____________num_ports = 12___________________

    # num_ports = 12
    # num_servers = int((num_ports ** 3) / 4)
    # num_switches = int(num_ports * num_ports * 5 / 4)
    #
    # fattree = topo.Fattree(num_ports)
    # fattree.plot(save=True)
    #
    # jellyfish = topo.Jellyfish(num_servers, num_switches, num_ports)
    # jellyfish.plot(save=True, mode=1)

    # _____________num_ports = 14___________________

    num_ports = 14
    num_servers = int((num_ports ** 3) / 4)
    num_switches = int(num_ports * num_ports * 5 / 4)

    fattree = topo.Fattree(num_ports)
    fattree.plot(save=True)

    jellyfish = topo.Jellyfish(num_servers, num_switches, num_ports)
    jellyfish.plot(save=True, mode=1)
