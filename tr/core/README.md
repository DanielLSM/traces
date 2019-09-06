the approach is as follows:

1)define what is the discretization: for 0.1 its 11^2
2)for one state compute all actions and make N_action new states for each state, so N_actions * 11²
3)reduce the N_actions * 11² back to 121 (11²) through a cost function
4)repeat 2) and 3) until end of horizon

Note: the number of actions depends on the number of slots available, so its always varying... In reality, lets say for A-Checks/C-Checks it depends on the number of slots,
so if at any day there are 3 slots, there are actually 4 actions: 0,1,2,3 slots

D check slots:
Every C check counts as a D cycle, and every D check counts as a C cycle, if it reaches a maximum of
D-END = 4, it phases out.

D-MAX : the 3rd or the 4th will be D check

when we do a D check, D-cycle resets to 1

its either when it reaches to 4 or when it reaches the maximum amount of days


C check slots:
0.0) All aircrafts are operating on day one. (unless it states a future date on OPERATION)
0) on C_initial, some of the planes are past their due dates in FH/FC/DY, this is not valid so they should immediatily go to maintenance. Then the quantity they passed after the C-ccheck, should be discounted on the next C-check. Columns C_TOLU-DY/FH/FC tell how much tolerance was used in the previous check. This value has to be subtracted for the next check and should not be used again on the planning horizon.: 1
1) you cannot do C-checks on peak season, unless they are specified on more_c_slots: 1
2) you cannot do C-checks on C_not_allowed, unless they are in more_c_slots: 1
3) you cannot assing 2 C-Checks at the same time, they need a 3 days time: (it depends on START DAY INTERVAL on ADDITIONAL sheet):1
4) you can not do C-checks at fridays?: false you can do on fridays, 3 slots
5) you can not do C-Checks in public holidays: true
6) you can not do C-checks in the weekends: true
6.1) on all other days, you can always do 3 C-Checks at the same time.: unless specified on MORE_C_SLOTS sheet: true
7) C-checks should be made ininterupt, C_elapsed_time indicates how many days an Aircraft needs to be on the C-check hangar. if the TAT is 13, it actually means 13+public_holidays+weekends, if the due date would end up in a peak season, without slot, or in a C_not allowed, without slot, then its not possible to schedule: true
8) on C_elapsed_time a TAT of -1, means a phase out, the aircraft stops working, so uppon the next time the aircraft ends FH, FC our DY, it stops operating and no longer needs maintenance.: true

A check slots:
0.0) All aircrafts are operating on day one.: (same as C-slots, need to check OPERATION on D-INTIAL) 
0) on A_initial, some of the planes are past their due dates in FH/FC/DY, this is now valid so they should immediatily go to maintenance. Then the quantity they passed after the C-ccheck, should be discounted on the next C-check. Columns A_TOLU-DY/FH/FC tell how much tolerance was used in the previous check. This value has to be subtracted for the next check and should not be used again on the planning horizon: true
1) you CAN do A-checks on peak season: true
2) you cannot do A-checks on A_not_allowed, unless they are in more_A_slots, more_A_slots does not add slots, just replaces them, you can only do a maximum of 2 A-sots at each time: true
3) you CAN assing 2 A-Checks at the same time: true (you can do 3 if one is merged with C-check)
4) you can not do A-checks at fridays(unless specified on A_more_slot)?: true
5) you can not do A-Checks in public holidays: true
6) you can not do A-checks in the weekends: true
6.1) on all other days, you can always do 1 A-Check at the same time: true
7) A-checks only take one day: true

Merge A with C-Checks:
When it is possible to merge an A-check with a C-check?
if a C-check is ongoing, and the aircraft is also highest-priority merge, otherwise, do not merge
