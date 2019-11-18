import numpy as np
from tqdm import tqdm
from collections import OrderedDict

from tr.core.utils import advance_date, save_pickle, load_pickle
from tr.core.tasks_planner import datetime_to_integer, integer_to_datetime

try:
    task_calendar = load_pickle("task_calendar.pkl")
except:
    raise "Tasks calendar file not found"

type_checks = ['A', 'C', 'C MERGED WITH A']

#### Per Hangar, Per Day
hangar_A = OrderedDict()
hangar_C = OrderedDict()
print("INFO: processing task metrics per hangar")
for date in tqdm(task_calendar.keys()):
    for type_check in task_calendar[date].keys():
        hangar_A[date] = OrderedDict()
        hangar_C[date] = OrderedDict()
        if type_check == 'A':
            hangar_A[date]['A'] = task_calendar[date]['A']
        elif type_check == 'C':
            hangar_C[date]['C'] = task_calendar[date]['C']
        elif type_check == 'C MERGED WITH A':
            hangar_C[date]['C MERGED WITH A'] = task_calendar[date]['C MERGED WITH A']

# 'aircraft': merged_A_with_C,
# 'tasks_per_aircraft': tasks_per_aircraft,
# 'ratios_per_aircraft': ratios_executed_per_aircraft,
# 'tasks_expected_due_dates_per_aircraft': tasks_expected_due_dates_per_aircraft
aircraft_A = OrderedDict()
full_distrib_A_ratios = OrderedDict()
days_wasted_A = OrderedDict()

for date in tqdm(hangar_A.keys()):
    # import ipdb
    # ipdb.set_trace()
    if 'A' in hangar_A[date].keys():
        aircraft_A[date] = hangar_A[date]['A']['aircraft']
        full_distrib_A_ratios[date] = []
        days_wasted_A[date] = []
        for ac in aircraft_A[date]:
            for task in hangar_A[date]['A']['ratios_per_aircraft'][ac].keys():
                task_ratio = hangar_A[date]['A']['ratios_per_aircraft'][ac][task]
                executed_due_date = hangar_A[date]['A']['tasks_per_aircraft'][ac][task]
                expected_due_date = hangar_A[date]['A']['tasks_expected_due_dates_per_aircraft'][
                    ac][task]

                executed_due_date = integer_to_datetime(int(executed_due_date))
                expected_due_date = integer_to_datetime(int(expected_due_date))
                days_wasted = (expected_due_date - executed_due_date).days
                full_distrib_A_ratios[date].append(task_ratio)
                days_wasted_A[date].append(days_wasted)
    else:
        aircraft_A[date] = False
        full_distrib_A_ratios[date] = False
        days_wasted_A[date] = False

aircraft_C = OrderedDict()
full_distrib_C_ratios = OrderedDict()
days_wasted_C = OrderedDict()

aircraft_A_merged_C = OrderedDict()
full_distrib_A_merged_C_ratios = OrderedDict()
days_wasted_A_merged_C = OrderedDict()

for date in tqdm(hangar_C.keys()):
    # import ipdb
    # ipdb.set_trace()
    if 'C' in hangar_C[date].keys():
        aircraft_C[date] = hangar_C[date]['C']['aircraft']
        full_distrib_C_ratios[date] = []
        days_wasted_C[date] = []
        for ac in aircraft_C[date]:
            for task in hangar_C[date]['C']['ratios_per_aircraft'][ac].keys():
                task_ratio = hangar_C[date]['C']['ratios_per_aircraft'][ac][task]
                executed_due_date = hangar_C[date]['C']['tasks_per_aircraft'][ac][task]
                expected_due_date = hangar_C[date]['C']['tasks_expected_due_dates_per_aircraft'][
                    ac][task]

                executed_due_date = integer_to_datetime(int(executed_due_date))
                expected_due_date = integer_to_datetime(int(expected_due_date))
                days_wasted = (expected_due_date - executed_due_date).days
                full_distrib_C_ratios[date].append(task_ratio)
                days_wasted_C[date].append(days_wasted)
    else:
        aircraft_C[date] = False
        full_distrib_C_ratios[date] = False
        days_wasted_C[date] = False
    if 'C MERGED WITH A' in hangar_C[date].keys():
        aircraft_A_merged_C[date] = hangar_C[date]['C MERGED WITH A']['aircraft']
        full_distrib_A_merged_C_ratios[date] = []
        days_wasted_A_merged_C[date] = []
        for ac in aircraft_A_merged_C[date]:
            for task in hangar_C[date]['C MERGED WITH A']['ratios_per_aircraft'][ac].keys():
                task_ratio = hangar_C[date]['C MERGED WITH A']['ratios_per_aircraft'][ac][task]
                executed_due_date = hangar_C[date]['C MERGED WITH A']['tasks_per_aircraft'][ac][
                    task]
                expected_due_date = hangar_C[date]['C MERGED WITH A'][
                    'tasks_expected_due_dates_per_aircraft'][ac][task]

                executed_due_date = integer_to_datetime(int(executed_due_date))
                expected_due_date = integer_to_datetime(int(expected_due_date))
                days_wasted = (expected_due_date - executed_due_date).days
                full_distrib_A_merged_C_ratios[date].append(task_ratio)
                days_wasted_A_merged_C[date].append(days_wasted)
    else:
        aircraft_A_merged_C[date] = False
        full_distrib_A_merged_C_ratios[date] = False
        days_wasted_A_merged_C[date] = False

import ipdb
ipdb.set_trace()
