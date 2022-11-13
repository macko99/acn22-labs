import topo

################################################################
##                                                            ##
##  script used for plotting the Fattree and Jellyfish topos  ##
##                                                            ##
################################################################
##                                                            ##
##  for fattree we have added 2 optional parameters:          ##
##      plot - if True the created topo will be ploted        ##
##      save - if True, plot will be saved as .png file       ##
##                                                            ##  
##  for jellyfish we have added 3 optional parameters:        ##
##      plot - if True the created topo will be ploted        ##
##      save - if True, plot will be saved as .png file       ##
##      mode - changes nodes layout, for better look          ## 
##                                                            ## 
################################################################

if __name__ == "__main__":
	
    #k - num_of_ports - as presented in lectures
    k = 4
    fattree = topo.Fattree(k, plot=True, save=True)
    jellyfish = topo.Jellyfish(int((k**3)/4), int(k*k*5/4), k, plot=True, save=True, mode=2)
    
    # k = 6
    # fattree = topo.Fattree(k, True, True)
    # jellyfish = topo.Jellyfish(int((k**3)/4), int(k*k*5/4), k, plot=True, save=True, mode=2)

    k = 8
    fattree = topo.Fattree(k, plot=True, save=True)
    jellyfish = topo.Jellyfish(int((k**3)/4), int(k*k*5/4), k, plot=True, save=True, mode=1)

    # k = 10
    # fattree = topo.Fattree(k, plot=True, save=True)
    # jellyfish = topo.Jellyfish(int((k**3)/4), int(k*k*5/4), k, plot=True, save=True, mode=1)

    # k = 12
    # fattree = topo.Fattree(k, plot=True, save=True)
    # jellyfish = topo.Jellyfish(int((k**3)/4), int(k*k*5/4), k, plot=True, save=True, mode=1)

    k = 14
    fattree = topo.Fattree(k, plot=True, save=True)
    jellyfish = topo.Jellyfish(int((k**3)/4), int(k*k*5/4), k, plot=True, save=True, mode=1)
