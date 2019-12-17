import numpy as np
from tqdm import tqdm
from collections import OrderedDict
import matplotlib.pyplot as plt

from tr.core.utils import advance_date, save_pickle, load_pickle
from tr.core.tasks_planner import datetime_to_integer, integer_to_datetime

try:
    final_fleet_schedule = {}
    task_calendar = load_pickle("build/output_files/task_calendar.pkl")
    processed_aircraft_tasks = load_pickle("build/tasks_files/processed_aircraft_tasks.pkl")
    final_fleet_schedule['A'] = load_pickle("build/check_files/final_schedule_A.pkl")
    final_fleet_schedule['C'] = load_pickle("build/check_files/final_schedule_C.pkl")
except:
    raise "Tasks calendar file not found"


def plot_MRI_distrib(aircraft,
                     calendar_check,
                     check_date,
                     baseline_days_before_check=0,
                     baseline_days_bar_bottom=-5,
                     check_type='A'):
    min_max_dates = {}
    for task in calendar_check['tasks_expected_due_dates_per_aircraft'][aircraft].keys():
        task_date = calendar_check['tasks_expected_due_dates_per_aircraft'][aircraft][task]
        task_date = integer_to_datetime(int(task_date))
        delta_days = (task_date - check_date).days
        min_max_dates[task] = delta_days
    work_package_tasks = sorted(min_max_dates, key=min_max_dates.get)
    work_package_delta_dates = [min_max_dates[task] for task in work_package_tasks]

    #min
    work_package_task_min = min(min_max_dates, key=min_max_dates.get)
    work_package_due_date = min_max_dates[work_package_task_min]
    work_task_min_date = calendar_check['tasks_expected_due_dates_per_aircraft'][aircraft][
        work_package_task_min]
    work_task_min_date = integer_to_datetime(int(work_task_min_date))

    #max
    work_package_task_max = max(min_max_dates, key=min_max_dates.get)
    work_package_due_date_max = min_max_dates[work_package_task_max]
    work_task_max_date = calendar_check['tasks_expected_due_dates_per_aircraft'][aircraft][
        work_package_task_max]
    work_task_max_date = integer_to_datetime(int(work_task_max_date))

    histogram_check_date = [baseline_days_before_check for x in work_package_delta_dates]
    histogram_work_package_due_date = [
        baseline_days_before_check + work_package_due_date for x in work_package_delta_dates
    ]
    histogram_work_package_expected_date = [
        baseline_days_before_check + x for x in work_package_delta_dates
    ]

    bars1_stacked = histogram_check_date
    bars2_stacked = [
        histogram_work_package_due_date[i] - histogram_check_date[i]
        for i in range(len(histogram_check_date))
    ]
    bars3_stacked = [
        histogram_work_package_expected_date[i] - histogram_work_package_due_date[i]
        for i in range(len(histogram_check_date))
    ]

    # counts, bins = np.histogram(list(min_max_dates.values()))
    bars3_bottom = np.add(bars1_stacked, bars2_stacked).tolist()
    baseline_days_bar_bottom = [baseline_days_bar_bottom for i in range(len(work_package_tasks))]
    # The position of the bars on the x-axis
    r = range(len(work_package_tasks))

    # Names of group and bar width
    names = work_package_tasks
    barWidth = 1

    # Create brown bars
    plt.bar(r,
            baseline_days_bar_bottom,
            bottom=bars1_stacked,
            color='#19CB06',
            edgecolor='white',
            width=barWidth)
    # Create green bars (middle), on top of the firs ones
    plt.bar(r,
            bars2_stacked,
            bottom=bars1_stacked,
            color='#CCCC00',
            edgecolor='white',
            width=barWidth)
    # Create green bars (top)
    a2 = plt.bar(r,
                 bars3_stacked,
                 bottom=bars3_bottom,
                 color='#FF8000',
                 edgecolor='white',
                 width=barWidth)

    # Custom X axis
    plt.title("{} due-dates per MRI on {}-check, on date {}".format(aircraft, check_type,
                                                                    check_date.date()))
    plt.xticks(r, names, fontweight='bold')
    plt.ylabel("Number of days from check execution")
    plt.xlabel("MRI Clusters anonymized codes")

    for i, v in enumerate(histogram_work_package_expected_date):
        plt.text(i - 0.05, v, str(v), color='blue', fontweight='bold')
    ###### Execution date
    plt.text(2,
             work_package_due_date_max - 3,
             "{}-check date {}".format(check_type, check_date.date()),
             color='#19CB06',
             fontweight='bold')

    ###### Workpackage due-date
    plt.text(2,
             work_package_due_date_max - 1.5,
             "WP due date {}".format(work_task_min_date.date()),
             color='#CCCC00',
             fontweight='bold')

    ###### Workpackage due-date
    plt.text(2,
             work_package_due_date_max,
             "Task due date {}".format(work_task_max_date.date()),
             color='#FF8000',
             fontweight='bold')

    # Show graphic
    plt.show()
    return work_package_delta_dates


def plot_MRI_distrib_per_aircraft(aircraft, check='A'):
    all_delta_dates_mris = []
    for check_date in final_fleet_schedule[check][aircraft].keys():
        calendar_check = task_calendar[check_date][check]
        assert aircraft in calendar_check['aircraft']
        work_package_delta_dates = plot_MRI_distrib(aircraft,
                                                    calendar_check,
                                                    check_date,
                                                    check_type=check)
        all_delta_dates_mris.extend(work_package_delta_dates)
    all_delta_dates_mris = [x for x in all_delta_dates_mris if x < 60]
    plt.clf()
    plt.cla()
    plt.close()
    plt.title("MRI clusters vs days past all {}-checks executions for {}".format(check, aircraft))
    plt.ylabel("Number of MRI clusters of tasks")
    plt.xlabel("MRI clusters number of days to due-date")
    plt.hist(all_delta_dates_mris, 50)
    plt.show()



plot_MRI_distrib_per_aircraft('Aircraft-1', check='A')
plot_MRI_distrib_per_aircraft('Aircraft-2', check='A')

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

