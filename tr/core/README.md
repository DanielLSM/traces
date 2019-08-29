the approach is as follows:

1)define what is the discretization: for 0.1 its 11^2
2)for one state compute all actions and make N_action new states for each state, so N_actions * 11²
3)reduce the N_actions * 11² back to 121 (11²) through a cost function
4)repeat 2) and 3) until end of horizon

Note: the number of actions depends on the number of slots available, so its always varying... In reality, lets say for A-Checks/C-Checks it depends on the number of slots,
so if at any day there are 3 slots, there are actually 4 actions: 0,1,2,3 slots
