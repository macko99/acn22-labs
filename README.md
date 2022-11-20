# Advanced Computer Networks 2022

This is the repository holding the code skeleton for the lab assignments for Advanced Computer Networks 2022 at VU Amsterdam.



## How to run lab2:

`python .\plot_topos.py`
(approx run time on M1 mac - 20 sec)

`python .\reproduce_1c.py`
(mean run time on M1 mac - 2 min 40 sec)

`python .\reproduce_9.py` (uses multiprocessing to speed up the process of generating the figure 9, by default it uses all available cores of your CPU)


## How to run lab3:

sudo ryu-manager ./sp_routing.py --observe-links