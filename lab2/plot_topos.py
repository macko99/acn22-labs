import topo


if __name__ == "__main__":
	
    k = 4
    fattree = topo.Fattree(k, True, True)
    jellyfish = topo.Jellyfish(int((k**3)/4), int(k*k*5/4), k, plot=True, save=True, mode=2)
    
    # k = 6
    # fattree = topo.Fattree(k, True, True)
    # jellyfish = topo.Jellyfish(int((k**3)/4), int(k*k*5/4), k, plot=True, save=True, mode=2)

    k = 8
    fattree = topo.Fattree(k, True, True)
    jellyfish = topo.Jellyfish(int((k**3)/4), int(k*k*5/4), k, plot=True, save=True, mode=1)

    # k = 10
    # fattree = topo.Fattree(k, True, True)
    # jellyfish = topo.Jellyfish(int((k**3)/4), int(k*k*5/4), k, plot=True, save=True, mode=1)

    # k = 12
    # fattree = topo.Fattree(k, True, True)
    # jellyfish = topo.Jellyfish(int((k**3)/4), int(k*k*5/4), k, plot=True, save=True, mode=1)

    k = 14
    fattree = topo.Fattree(k, True, True)
    jellyfish = topo.Jellyfish(int((k**3)/4), int(k*k*5/4), k, plot=True, save=True, mode=1)
