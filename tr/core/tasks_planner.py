# So we are going to solve the task packaging problem as a bin packaging problem.
# Each day is a bin and we can compute à priori all the bins and their limits in man-hours
# for A checks is trivial and we keep assigining until limits are reached
# for C checks, when a C check starts, bins are created each day, then ordered
# the order of the bins is: fill the ones with least amount of aircrafts assigned first
import numpy as np
import pandas as pd
from copy import deepcopy


from datetime import datetime, date
from collections import OrderedDict
from tqdm import tqdm

from tr.core.utils import advance_date, save_pickle, load_pickle


def datetime_to_integer(dt_time):

    # TODO: SOLVE FOR OLD DATA FIRST
    if not isinstance(dt_time, pd.Timestamp) \
        and not isinstance(dt_time, pd.DatetimeIndex) \
            and not isinstance(dt_time, date):
        return np.nan

    return 10000 * dt_time.year + 100 * dt_time.month + dt_time.day


def integer_to_datetime(dt_time):
    dt_time = str(dt_time)
    try:
        date = pd.to_datetime(dt_time)
    except:
        import ipdb
        ipdb.set_trace()
    return date


def update(lastexecdate, Simulatedlifetime):
    if type(lastexecdate) == int or type(lastexecdate) == float or isinstance(
            lastexecdate, np.float64) == True:
        value = lastexecdate
    else:
        value = datetime_to_integer(lastexecdate)

    # We need to find at what index is the value equal to last exec date
    idx = np.where(Simulatedlifetime[0, :] == value)

    COPY = deepcopy(Simulatedlifetime)
    # Setting the array at 0 at these locations
    FH = COPY[1, idx[0][0]]
    FC = COPY[2, idx[0][0]]
    Days = COPY[3, idx[0][0]]
    months = COPY[6, idx[0][0]]
    COPY[1, :] = COPY[1, :] - FH
    COPY[2, :] = COPY[2, :] - FC
    COPY[3, :] = COPY[3, :] - Days
    COPY[6, :] = COPY[3, :] - months

    return COPY


class TasksPlanner:
    def __init__(self, aircraft_tasks, aircraft_info, df_tasks, skills, skills_ratios_A,
                 skills_ratios_C, man_hours, delivery, df_aircraft_shaved):
        self.aircraft_tasks = aircraft_tasks
        self.aircraft_info = aircraft_info
        self.df_aircraft_shaved = df_aircraft_shaved
        self.df_tasks = df_tasks
        self.skills = skills
        self.skills_ratios_A = skills_ratios_A
        self.skills_ratios_C = skills_ratios_C
        self.man_hours = man_hours
        self.delivery = delivery

        try:
            self.final_calendar = {}
            self.final_fleet_schedule = {}
            self.final_calendar['A'] = load_pickle(
                "build/check_files/calendar_A.pkl")
            self.final_calendar['C'] = load_pickle(
                "build/check_files/calendar_C.pkl")

            # TODO you need to include the merged A to C checks, its kinda  important to know
            # which ones are merged
            self.final_fleet_schedule['A'] = load_pickle(
                "build/check_files/final_schedule_A.pkl")
            self.final_fleet_schedule['C'] = load_pickle(
                "build/check_files/final_schedule_C.pkl")
        except:
            raise "No check plannings found, please run checks first"

        try:
            self.processed_aircraft_tasks = load_pickle(
                "build/tasks_files/processed_aircraft_tasks.pkl")
        except:
            self.processed_aircraft_tasks = self._process_aircraft_tasks()
            save_pickle(self.processed_aircraft_tasks,
                        "build/tasks_files/processed_aircraft_tasks.pkl")

        try:
            self.task_calendar = load_pickle(
                "build/output_files/task_calendar.pkl")
        except:
            print("INFO: no previous tasks planning information")

        print("INFO: tasks planner finished with sucess")

    def task_calendar_to_excel(self):
        task_calendar = self.task_calendar

        print("INFO: Saving tasks excel files")
        for ac in tqdm(self.processed_aircraft_tasks.keys()):
            processed_aircraft_tasks = self.processed_aircraft_tasks[ac]
            df_aircraft = processed_aircraft_tasks['df_aircraft_shaved_tasks']
            a_check_dates = deepcopy(
                processed_aircraft_tasks['a_checks_dates'])
            c_check_dates = deepcopy(
                processed_aircraft_tasks['c_checks_dates'])
            c_check_dates_end = processed_aircraft_tasks['c_checks_dates_end']
            merged_a_c_check = []

            for date in a_check_dates:
                if date in c_check_dates:
                    merged_a_c_check.append(date)
            for date in merged_a_c_check:
                a_check_dates.remove(date)
                c_check_dates.remove(date)

            full_dates_a = {integer_to_datetime(
                x): 'A-CHECK' for x in a_check_dates}
            full_dates_c = {integer_to_datetime(
                x): 'C-CHECK' for x in c_check_dates}
            full_merged = {integer_to_datetime(
                x): 'MERGED' for x in merged_a_c_check}
            full_merged.update(full_dates_a)
            full_merged.update(full_dates_c)
            full_merged_sorted = sorted(
                full_merged.items(), key=lambda kv: kv[0])
            full_merged_sorted = OrderedDict(full_merged_sorted)

            print("INFO: Saving {} task and check planning".format(ac))
            dict1 = OrderedDict()
            dict1['A/C ID'] = []
            dict1['MAINTENANCE OPPORTUNITY'] = []
            dict1['START'] = []
            dict1['END'] = []
            dict1['ITEM CLUSTER'] = []
            if 'REF AIRLINE' in df_aircraft.keys():
                dict1['REF AIRLINE'] = []
                dict1['DESCRIPTION'] = []
            dict1['BLOCK'] = []
            dict1['SKILL'] = []
            dict1['TASK BY BLOCK'] = []

            for check in full_merged_sorted.keys():
                check_date = integer_to_datetime(check)
                type_check = full_merged_sorted[check]
                if type_check == 'A-CHECK':
                    type_check = 'A'
                elif type_check == 'C-CHECK':
                    type_check = 'C'
                elif type_check == 'MERGED':
                    type_check = 'C MERGED WITH A'
                assert ac in task_calendar[check_date][type_check]['tasks_per_aircraft'].keys(
                )
                if full_merged_sorted[check] == 'A-CHECK':
                    start = check_date.date().isoformat()
                    end = check_date.date().isoformat()
                    code = self.final_fleet_schedule['A'][ac][check_date]['STATE']['A-SN']
                    code = 'A ' + str(code)
                elif full_merged_sorted[check] == 'C-CHECK':
                    idx_check = processed_aircraft_tasks['c_checks_dates'].index(
                        check_date)
                    date_end = processed_aircraft_tasks['c_checks_dates_end'][idx_check]
                    start = check_date.date().isoformat()
                    end = date_end.date().isoformat()
                    code = self.final_fleet_schedule['C'][ac][check_date]['STATE']['C-SN']
                    code = 'C ' + str(code)
                elif full_merged_sorted[check] == 'MERGED':
                    try:
                        idx_check = processed_aircraft_tasks['c_checks_dates'].index(
                            check_date)
                    except:
                        import ipdb
                        ipdb.set_trace()
                    date_end = processed_aircraft_tasks['c_checks_dates_end'][idx_check]
                    start = check_date.date().isoformat()
                    end = date_end.date().isoformat()
                    code_a = self.final_fleet_schedule['A'][ac][check_date]['STATE']['A-SN']
                    code_c = self.final_fleet_schedule['C'][ac][check_date]['STATE']['C-SN']
                    code = 'C ' + code_c + ' + A ' + code_a

                for task in task_calendar[check_date][type_check]['tasks_per_aircraft'][ac].keys():
                    idx_from_task_number = np.where(
                        df_aircraft['NR TASK'] == task)[0][0]
                    i = idx_from_task_number
                    item = df_aircraft['ITEM'].iat[i]
                    if 'REF AIRLINE' in df_aircraft.keys():
                        ref_tap = df_aircraft['REF TAP'].iat[i]
                        description = df_aircraft['DESCRIPTION'].iat[i]
                    skill = df_aircraft['SKILL'].iat[i]
                    block = df_aircraft['TASK BY BLOCK'].iat[i]

                    dict1['A/C ID'].append(ac)
                    dict1['MAINTENANCE OPPORTUNITY'].append(code)
                    dict1['START'].append(start)
                    dict1['END'].append(end)
                    dict1['ITEM CLUSTER'].append(item)
                    if 'REF AIRLINE' in df_aircraft.keys():
                        dict1['REF AIRLINE'].append(ref_tap)
                        dict1['DESCRIPTION'].append(description)
                    dict1['BLOCK'].append(block)
                    dict1['SKILL'].append(skill)
                    dict1['TASK BY BLOCK'].append(block)

            df = pd.DataFrame(dict1, columns=dict1.keys())

            len(df)
            df.to_excel('task_planning/tasks-{}.xlsx'.format(ac))
            print("INFO: Saving tasks excel files")

    def solve_man_hours(self, task_calendar):
        pass

    def solve_tasks(self):
        task_calendar = OrderedDict()
        processed_aircraft_tasks = deepcopy(self.processed_aircraft_tasks)
        for date in tqdm(self.final_calendar['A'].keys()):
            day_state_A = self.final_calendar['A'][date]
            day_state_C = self.final_calendar['C'][date]
            task_calendar[date] = {}
            merged_A_with_C = []

            if day_state_A['MAINTENANCE']:
                aircraft_A = day_state_A['ASSIGNMENT']

            if day_state_C['MAINTENANCE']:
                aircraft_C = day_state_C['ASSIGNMENT']
                aircraft_C = aircraft_C if isinstance(
                    aircraft_C, list) else [aircraft_C]

            if day_state_A['MERGED FLAG']:
                for aircraft_merged_c in aircraft_C:
                    if aircraft_merged_c in aircraft_A:
                        merged_A_with_C.append(aircraft_merged_c)
                        aircraft_A.remove(aircraft_merged_c)
                for merged_ac in merged_A_with_C:
                    aircraft_C.remove(merged_ac)

            if day_state_A['MAINTENANCE']:
                # do usual maintenance on all A-tasks
                if len(aircraft_A) != 0:
                    processed_aircraft_tasks, tasks_per_aircraft, ratios_executed_per_aircraft, tasks_expected_due_dates_per_aircraft = self.process_maintenance_day(
                        processed_aircraft_tasks, aircraft_A, date, type_check='A-CHECK')
                    task_calendar[date]['A'] = {
                        'aircraft': aircraft_A,
                        'tasks_per_aircraft': tasks_per_aircraft,
                        'ratios_per_aircraft': ratios_executed_per_aircraft,
                        'tasks_expected_due_dates_per_aircraft': tasks_expected_due_dates_per_aircraft
                    }

            if day_state_C['MAINTENANCE']:
                # do usual maintenance on all tasks
                if len(aircraft_C) != 0:
                    processed_aircraft_tasks, tasks_per_aircraft, ratios_executed_per_aircraft, tasks_expected_due_dates_per_aircraft = self.process_maintenance_day(
                        processed_aircraft_tasks, aircraft_C, date, type_check='C-CHECK')
                    task_calendar[date]['C'] = {
                        'aircraft': aircraft_C,
                        'tasks_per_aircraft': tasks_per_aircraft,
                        'ratios_per_aircraft': ratios_executed_per_aircraft,
                        'tasks_expected_due_dates_per_aircraft': tasks_expected_due_dates_per_aircraft
                    }
                if len(merged_A_with_C) != 0:
                    processed_aircraft_tasks, tasks_per_aircraft, ratios_executed_per_aircraft, tasks_expected_due_dates_per_aircraft = self.process_maintenance_day(
                        processed_aircraft_tasks, merged_A_with_C, date, type_check='ALL')
                    task_calendar[date]['C MERGED WITH A'] = {
                        'aircraft': merged_A_with_C,
                        'tasks_per_aircraft': tasks_per_aircraft,
                        'ratios_per_aircraft': ratios_executed_per_aircraft,
                        'tasks_expected_due_dates_per_aircraft': tasks_expected_due_dates_per_aircraft
                    }

        self.task_calendar = task_calendar
        return task_calendar

    # lets solve the inventorization first
    def process_maintenance_day(self,
                                processed_aircraft_tasks,
                                aircraft,
                                date,
                                type_check='A-CHECK'):
        tasks_per_aircraft = OrderedDict()
        ratios_executed_per_aircraft = OrderedDict()
        tasks_expected_due_dates_per_aircraft = OrderedDict()

        for ac in aircraft:
            df_ac = processed_aircraft_tasks[ac]['df_aircraft_shaved_tasks']
            if type_check == 'A-CHECK' or type_check == 'ALL':
                idx_check = processed_aircraft_tasks[ac]['a_checks_dates'].index(
                    date)
                previous_check_start = processed_aircraft_tasks[ac]['a_checks_dates'][idx_check]
                previous_check = processed_aircraft_tasks[ac]['a_checks_dates'][idx_check]
                previous_check = datetime_to_integer(previous_check)
                previous_check_start = datetime_to_integer(
                    previous_check_start)

                if date != processed_aircraft_tasks[ac]['a_checks_dates'][-1]:
                    next_check = processed_aircraft_tasks[ac]['a_checks_dates'][idx_check + 1]
                    next_check = datetime_to_integer(next_check)
                else:
                    # make a next check based on the the time from the last one
                    # find number of days between last a-checks
                    ultimo_check = integer_to_datetime(
                        processed_aircraft_tasks[ac]['a_checks_dates'][-1])
                    penultimo_check = integer_to_datetime(
                        processed_aircraft_tasks[ac]['a_checks_dates'][-2])
                    try:
                        days = (ultimo_check - penultimo_check).days
                        next_check = advance_date(ultimo_check, days=days)
                        next_check = datetime_to_integer(next_check)
                    except:
                        import ipdb
                        ipdb.set_trace()

                if type_check == 'ALL':
                    next_check_a = next_check

            #######################################################################################
            if type_check == 'C-CHECK' or type_check == 'ALL':
                idx_check = processed_aircraft_tasks[ac]['c_checks_dates'].index(
                    date)
                previous_check_start = processed_aircraft_tasks[ac]['c_checks_dates'][idx_check]
                previous_check = processed_aircraft_tasks[ac]['c_checks_dates_end'][idx_check]
                previous_check = datetime_to_integer(previous_check)
                previous_check_start = datetime_to_integer(
                    previous_check_start)

                if date != processed_aircraft_tasks[ac]['c_checks_dates'][-1]:
                    next_check = processed_aircraft_tasks[ac]['c_checks_dates'][idx_check + 1]
                    next_check = datetime_to_integer(next_check)

                else:
                    # make a next check based on the the time from the last one
                    # find number of days between last c-checks
                    ultimo_check = integer_to_datetime(
                        processed_aircraft_tasks[ac]['c_checks_dates'][-1])
                    if len(processed_aircraft_tasks[ac]['c_checks_dates']) != 1:
                        penultimo_check = integer_to_datetime(
                            processed_aircraft_tasks[ac]['c_checks_dates'][-2])
                        days = (ultimo_check - penultimo_check).days
                        next_check = advance_date(ultimo_check, days=days)
                        next_check = datetime_to_integer(next_check)
                    else:
                        next_check = advance_date(ultimo_check, days=700)
                        next_check = datetime_to_integer(next_check)
                if type_check == 'ALL':
                    next_check_c = next_check

            tasks_executed = []
            ratios_executed = []
            tasks_expected_due_dates = []
            for task_number in processed_aircraft_tasks[ac]['expected_due_dates'].keys():
                expected_due_date = processed_aircraft_tasks[ac]['expected_due_dates'][task_number]
                try:
                    last_executed_date = processed_aircraft_tasks[ac]['last_executed_value'][
                        task_number]
                except:
                    last_executed_date = expected_due_date

                if last_executed_date != expected_due_date:
                    ratio_exec = self.compute_ratio_executed(last_executed_date,
                                                             previous_check_start,
                                                             expected_due_date)
                else:
                    ratio_exec = False

                expected_due_date = processed_aircraft_tasks[ac]['expected_due_dates'][task_number]
                block = df_ac[df_ac['NR TASK'] ==
                              task_number]['TASK BY BLOCK'][task_number]
                if (type_check == 'ALL'):
                    if block == 'A-CHECK':
                        if previous_check <= expected_due_date <= next_check_a:
                            tasks_executed.append(
                                (task_number, previous_check))
                            ratios_executed.append((task_number, ratio_exec))
                            tasks_expected_due_dates.append(
                                (task_number, expected_due_date))
                    elif block == 'C-CHECK':
                        if previous_check <= expected_due_date <= next_check_c:
                            tasks_executed.append(
                                (task_number, previous_check))
                            ratios_executed.append((task_number, ratio_exec))
                            tasks_expected_due_dates.append(
                                (task_number, expected_due_date))

                ############################################################################
                elif type_check == block:
                    expected_due_date = processed_aircraft_tasks[ac]['expected_due_dates'][
                        task_number]
                    if previous_check <= expected_due_date <= next_check:
                        tasks_executed.append((task_number, previous_check))
                        ratios_executed.append((task_number, ratio_exec))
                        tasks_expected_due_dates.append(
                            (task_number, expected_due_date))

            tasks_per_aircraft[ac] = dict(tasks_executed)
            ratios_executed_per_aircraft[ac] = dict(ratios_executed)
            tasks_expected_due_dates_per_aircraft[ac] = dict(
                tasks_expected_due_dates)
            assert len(tasks_expected_due_dates_per_aircraft[ac]) == len(
                tasks_per_aircraft[ac])
            processed_aircraft_tasks = self.reschedule_tasks(processed_aircraft_tasks, ac,
                                                             tasks_per_aircraft[ac])
        return processed_aircraft_tasks, tasks_per_aircraft, ratios_executed_per_aircraft, tasks_expected_due_dates_per_aircraft

    # this expected due date already has in account the.... min of fh blablabla in either
    # computed or rescheduled stuff
    def compute_ratio_executed(self, last_executed_date, previous_check, expected_due_date):
        last_executed_time = integer_to_datetime(int(last_executed_date))
        previous_check_time = integer_to_datetime(int(previous_check))
        expected_due_date_time = integer_to_datetime(int(expected_due_date))
        interval_max_days = (expected_due_date_time - last_executed_time).days
        actual_days = (previous_check_time - last_executed_time).days

        ratio = actual_days / interval_max_days

        return ratio

    # c_check is more complex, you got to figure it out
    def reschedule_tasks(self, processed_aircraft_tasks, ac, tasks_executed):

        # TODO: we need to check here if we reschdule from the last day of the c-check
        df_aircraft_shaved_tasks = processed_aircraft_tasks[ac]['df_aircraft_shaved_tasks']
        simulated_lifetime = processed_aircraft_tasks[ac]['simulated_lifetime']

        for task_executed in tasks_executed.keys():

            last_exec_value = tasks_executed[task_executed]

            idx = np.where(simulated_lifetime[0, :] == last_exec_value)
            TaskHorizon = update(last_exec_value, simulated_lifetime)
            TaskHorizon = TaskHorizon[:, idx[0][0] + 1:]

            idx_from_task_number = np.where(
                df_aircraft_shaved_tasks['NR TASK'] == task_executed)[0][0]
            i = idx_from_task_number

            # option 1 task has multiple FH/FC/CALmonths/Caldays
            fh_limit = df_aircraft_shaved_tasks['PER FH'].iat[i]
            fc_limit = df_aircraft_shaved_tasks['PER FC'].iat[i]
            cal_months_limit = df_aircraft_shaved_tasks['PER MONTH'].iat[i]
            cal_days_limit = df_aircraft_shaved_tasks['PER DAY'].iat[i]
            if fh_limit != 0 or fc_limit != 0 or cal_months_limit != 0 or cal_days_limit != 0:
                sorted_list = []
                if fh_limit != 0:
                    due_date_idx = np.searchsorted(
                        TaskHorizon[1, :], fh_limit, side='right')
                    sorted_list.append(due_date_idx)
                if fc_limit != 0:
                    due_date_idx = np.searchsorted(
                        TaskHorizon[2, :], fc_limit, side='right')
                    sorted_list.append(due_date_idx)
                if cal_months_limit != 0:
                    idx10 = np.where(
                        simulated_lifetime[0, :] == TaskHorizon[0, 0])[0][0]
                    dayz = int(simulated_lifetime[0, idx10 - 1]) % 100
                    sorted_list.append(np.searchsorted(
                        TaskHorizon[6, :], cal_months_limit) + dayz)
                if cal_days_limit != 0:
                    due_date_idx = cal_days_limit - 1
                    sorted_list.append(due_date_idx)

                min_due_date = int(min(sorted_list) - 1)
                # big big mistake
                # expected_due_date = simulated_lifetime[0, min_due_date]
                expected_due_date = TaskHorizon[0, min_due_date]
                processed_aircraft_tasks[ac]['expected_due_dates'][
                    task_executed] = expected_due_date
                processed_aircraft_tasks[ac]['last_executed_value'][task_executed] = last_exec_value
                # import ipdb
                # ipdb.set_trace()
            else:
                raise "So this doesnt makes sense!"

        return processed_aircraft_tasks

    def _process_aircraft_tasks(self):
        print("INFO: processing aircraft tasks")
        processed_aircraft_tasks = OrderedDict()
        for aircraft in tqdm(self.aircraft_tasks.keys()):
            simulated_lifetime, a_checks_dates, c_checks_dates, c_checks_dates_end = self.simulate_lifetime(
                aircraft)
            df_aircraft_shaved_tasks, FH_outlast, FC_outlast, DT_outlast, last_executed = self.process_not_null_tasks(
                aircraft)
            due_dates_dict, calculated_due_dates, typetask, unscheduled_task, cancer_tasks, last_executed_list = self.compute_initial_tasks_due_dates(
                df_aircraft_shaved_tasks, FH_outlast, FC_outlast, DT_outlast, last_executed,
                simulated_lifetime, a_checks_dates, c_checks_dates, c_checks_dates_end)
            processed_aircraft_tasks[aircraft] = {
                'simulated_lifetime': simulated_lifetime,
                'expected_due_dates': due_dates_dict,
                'df_aircraft_shaved_tasks': df_aircraft_shaved_tasks,
                'a_checks_dates': a_checks_dates,
                'c_checks_dates': c_checks_dates,
                'c_checks_dates_end': c_checks_dates_end,
                'calculated_due_dates': calculated_due_dates,
                'typetask': typetask,
                'unscheduled_task': unscheduled_task,
                'cancer_tasks': cancer_tasks,
                'last_executed_value': last_executed_list
            }
        return processed_aircraft_tasks

    def compute_initial_tasks_due_dates(self, df_aircraft_shaved_tasks, FH_outlast, FC_outlast,
                                        DT_outlast, last_executed, simulated_lifetime,
                                        a_checks_dates, c_checks_dates, c_checks_dates_end):
        calculated_due_dates = []
        expected_due_dates = []
        unscheduled_task = []
        typetask = []
        cancer_tasks = []
        last_executed_list = []
        for i in range(len(df_aircraft_shaved_tasks)):
            # option 1
            if i in DT_outlast:
                last_exec_value = df_aircraft_shaved_tasks['LAST EXEC DT'].iat[i]
                last_exec_value = last_exec_value.date()
                last_exec_value = datetime_to_integer(last_exec_value)
                if last_exec_value > last_executed:
                    raise ValueError('This task should DT be below 2018-07-26')
                    continue
                idx = np.where(simulated_lifetime[0, :] == last_exec_value)
                temp = df_aircraft_shaved_tasks['LAST EXEC DT'].iat[i]
                temp = temp.date()
                TaskHorizon = update(temp, simulated_lifetime)
                TaskHorizon = TaskHorizon[:, idx[0][0] + 1:]
            elif (i in FH_outlast) or (i in FC_outlast):
                comparison_dates = []
                if i in FH_outlast:
                    last_exec_margin = np.where(
                        simulated_lifetime[1, :] > df_aircraft_shaved_tasks['LAST EXEC FH'].iat[i])
                    last_exec_value = simulated_lifetime[0,
                                                         last_exec_margin[0][0] - 1]
                    comparison_dates.append(last_exec_margin)
                if i in FC_outlast:
                    last_exec_margin = np.where(
                        simulated_lifetime[2, :] > df_aircraft_shaved_tasks['LAST EXEC FC'].iat[i])
                    last_exec_value = simulated_lifetime[0,
                                                         last_exec_margin[0][0] - 1]
                    comparison_dates.append(last_exec_margin)
                value = min(comparison_dates)
                idx = np.where(simulated_lifetime[0, :] == value)
                TaskHorizon = update(value, simulated_lifetime)
                TaskHorizon = TaskHorizon[:, idx[0][0] + 1:]
                # TODO continue the task extravaganza
            else:
                # option 5 no dates given, using limits
                if not pd.isna(df_aircraft_shaved_tasks['LAST EXEC DT'].iat[i]) or not pd.isna(
                        df_aircraft_shaved_tasks['LAST EXEC FH'].iat[i]) or not pd.isna(
                            df_aircraft_shaved_tasks['LAST EXEC FC'].iat[i]):
                    comparison_dates = []
                    if not pd.isna(df_aircraft_shaved_tasks['LAST EXEC DT'].iat[i]):
                        last_exec_value = df_aircraft_shaved_tasks['LAST EXEC DT'].iat[i]
                        last_exec_value = last_exec_value.date()
                        last_exec_value = datetime_to_integer(last_exec_value)
                        comparison_dates.append(last_exec_value)
                    if not pd.isna(df_aircraft_shaved_tasks['LAST EXEC FH'].iat[i]):
                        last_exec_margin = np.where(simulated_lifetime[1, :] >
                                                    df_aircraft_shaved_tasks['LAST EXEC FH'].iat[i])
                        last_exec_value = simulated_lifetime[0,
                                                             last_exec_margin[0][0] - 1]
                        comparison_dates.append(last_exec_value)
                    if not pd.isna(df_aircraft_shaved_tasks['LAST EXEC FC'].iat[i]):
                        last_exec_margin = np.where(simulated_lifetime[2, :] >
                                                    df_aircraft_shaved_tasks['LAST EXEC FC'].iat[i])
                        last_exec_value = simulated_lifetime[0,
                                                             last_exec_margin[0][0] - 1]
                        comparison_dates.append(last_exec_value)
                    last_exec_value = min(comparison_dates)
                    if last_exec_value > last_executed:
                        if df_aircraft_shaved_tasks['TASK BY BLOCK'].iat[i] == 'C_CHECK':
                            if last_exec_value < c_checks_dates[0]:
                                calculated_due_dates.append(
                                    integer_to_datetime(int(last_exec_value)))
                                idx = np.where(
                                    simulated_lifetime[0, :] == c_checks_dates[-1])[0][0]
                                # randomly advancing 1000 days...
                                idx = idx + 1000
                                expected_due_date = simulated_lifetime[0, idx]
                                number_of_task = df_aircraft_shaved_tasks['NR TASK'].iat[i]
                                item_of_task = df_aircraft_shaved_tasks['ITEM'].iat[i]
                                assert isinstance(expected_due_date, float)
                                expected_due_dates.append(
                                    (number_of_task, expected_due_date))
                                typetask.append('C-Task')
                                unscheduled_task.append(item_of_task)
                                continue
                            else:
                                assert isinstance(expected_due_date, float)
                                expected_due_dates.append(
                                    (number_of_task, last_exec_value))
                                continue
                            assert isinstance(expected_due_date, float)
                            expected_due_dates.append(
                                (number_of_task, last_exec_value))
                            continue
                    idx = np.where(simulated_lifetime[0, :] == last_exec_value)
                    TaskHorizon = update(last_exec_value, simulated_lifetime)
                    TaskHorizon = TaskHorizon[:, idx[0][0] + 1:]
                else:
                    # le bullshit special
                    calculated_due_dates.append(
                        integer_to_datetime(int(last_exec_value)))
                    try:
                        idx = np.where(simulated_lifetime[0, :] == datetime_to_integer(
                            c_checks_dates[-1]))[0][0]
                    except:
                        import ipdb
                        ipdb.set_trace()
                    idx = idx + 1000  # randomly advancing 1000 days...
                    expected_due_date = simulated_lifetime[0, idx]
                    number_of_task = df_aircraft_shaved_tasks['NR TASK'].iat[i]
                    item_of_task = df_aircraft_shaved_tasks['ITEM'].iat[i]
                    task_by_block = df_aircraft_shaved_tasks['TASK BY BLOCK'].iat[i]
                    assert isinstance(expected_due_date, float)
                    expected_due_dates.append(
                        (number_of_task, expected_due_date))
                    typetask.append(task_by_block)
                    unscheduled_task.append(item_of_task)
                    continue
            # option 1 task has multiple FH/FC/CALmonths/Caldays
            number_of_task = df_aircraft_shaved_tasks['NR TASK'].iat[i]
            last_executed_value = TaskHorizon[0, 0]
            last_executed_list.append((number_of_task, last_executed_value))

            fh_limit = df_aircraft_shaved_tasks['PER FH'].iat[i]
            fc_limit = df_aircraft_shaved_tasks['PER FC'].iat[i]
            cal_months_limit = df_aircraft_shaved_tasks['PER MONTH'].iat[i]
            cal_days_limit = df_aircraft_shaved_tasks['PER DAY'].iat[i]
            if fh_limit != 0 or fc_limit != 0 or cal_months_limit != 0 or cal_days_limit != 0:
                sorted_list = []
                if fh_limit != 0:
                    due_date_idx = np.searchsorted(
                        TaskHorizon[1, :], fh_limit, side='right')
                    sorted_list.append(due_date_idx)
                if fc_limit != 0:
                    due_date_idx = np.searchsorted(
                        TaskHorizon[2, :], fc_limit, side='right')
                    sorted_list.append(due_date_idx)
                if cal_months_limit != 0:
                    idx10 = np.where(
                        simulated_lifetime[0, :] == TaskHorizon[0, 0])[0][0]
                    dayz = int(simulated_lifetime[0, idx10 - 1]) % 100
                    sorted_list.append(np.searchsorted(
                        TaskHorizon[6, :], cal_months_limit) + dayz)
                if cal_days_limit != 0:
                    due_date_idx = cal_days_limit - 1
                    sorted_list.append(due_date_idx)

                min_due_date = int(min(sorted_list) - 1)
                # last_exec_value = min(comparison_dates)
                if df_aircraft_shaved_tasks['TASK BY BLOCK'].iat[i] == 'C_CHECK':
                    if TaskHorizon[0, min_due_date] < datetime_to_integer(c_checks_dates[0]):
                        calculated_due_dates.append(
                            integer_to_datetime(int(last_exec_value)))
                        idx = np.where(
                            simulated_lifetime[0, :] == c_checks_dates[-1])[0][0]
                        idx = idx + 1000  # randomly advancing 1000 days...
                        expected_due_date = simulated_lifetime[0, idx]
                        number_of_task = df_aircraft_shaved_tasks['NR TASK'].iat[i]
                        item_of_task = df_aircraft_shaved_tasks['ITEM'].iat[i]
                        assert isinstance(expected_due_date, float)
                        expected_due_dates.append(
                            (number_of_task, expected_due_date))
                        typetask.append('C-Task')
                        unscheduled_task.append(item_of_task)
                    else:
                        assert isinstance(TaskHorizon[0, min_due_date], float)
                        expected_due_dates.append(
                            (number_of_task, TaskHorizon[0, min_due_date]))
                elif TaskHorizon[0, min_due_date] < datetime_to_integer(a_checks_dates[0]):
                    if len(c_checks_dates) != 0:  # TODO double check this please
                        if TaskHorizon[0, min_due_date] < datetime_to_integer(c_checks_dates[0]):
                            calculated_due_dates.append(
                                integer_to_datetime(int(last_exec_value)))
                            idx = np.where(simulated_lifetime[0, :] == datetime_to_integer(
                                c_checks_dates[-1]))[0][0]
                            idx = idx + 1000  # randomly advancing 1000 days...
                            expected_due_date = simulated_lifetime[0, idx]
                            number_of_task = df_aircraft_shaved_tasks['NR TASK'].iat[i]
                            item_of_task = df_aircraft_shaved_tasks['ITEM'].iat[i]
                            assert isinstance(expected_due_date, float)
                            expected_due_dates.append(
                                (number_of_task, expected_due_date))
                            typetask.append('A-Task')
                            unscheduled_task.append(item_of_task)
                            continue
                        else:
                            assert isinstance(
                                TaskHorizon[0, min_due_date], float)
                            expected_due_dates.append(
                                (number_of_task, TaskHorizon[0, min_due_date]))
                            continue
                    item_of_task = df_aircraft_shaved_tasks['ITEM'].iat[i]
                    number_of_task = df_aircraft_shaved_tasks['NR TASK'].iat[i]
                    cancer_tasks.append(item_of_task)
                else:
                    number_of_task = df_aircraft_shaved_tasks['NR TASK'].iat[i]
                    assert isinstance(TaskHorizon[0, min_due_date], float)
                    expected_due_dates.append(
                        (number_of_task, TaskHorizon[0, min_due_date]))

        # import ipdb
        # ipdb.set_trace()
        due_dates_dict = dict(expected_due_dates)
        last_executed_dict = dict(last_executed_list)
        return due_dates_dict, calculated_due_dates, typetask, unscheduled_task, cancer_tasks, last_executed_dict

    def process_not_null_tasks(self, aircraft):
        def find_last_exectued(df_aircraft_shaved_tasks, aircraft):
            temporary_tasks = self.df_tasks[self.df_tasks['A/C'] == aircraft]
            temporary_tasks = temporary_tasks.reset_index(drop=True)
            n_temporary_tasks = len(temporary_tasks['LAST EXEC DT'])
            last_executed = 0
            for i in range(n_temporary_tasks):

                if type(temporary_tasks['LAST EXEC DT'][i]) == str:
                    try:
                        temp = temporary_tasks['LAST EXEC DT'][i].date()
                        temp = datetime_to_integer(temp)
                    except Exception as e:
                        raise(e)
                else:
                    temp = datetime_to_integer(
                        temporary_tasks['LAST EXEC DT'][i])
                if temp > last_executed:
                    last_executed = temp
            return last_executed

        df_aircraft_shaved_tasks = deepcopy(self.df_aircraft_shaved[aircraft])
        last_executed = find_last_exectued(df_aircraft_shaved_tasks, aircraft)
        df_aircraft_shaved_tasks = df_aircraft_shaved_tasks.drop_duplicates(
            ['ITEM'], keep='first')
        FH_outlast = np.where(
            df_aircraft_shaved_tasks['LAST EXEC FH'].notnull())[0]
        FC_outlast = np.where(
            df_aircraft_shaved_tasks['LAST EXEC FC'].notnull())[0]
        DT_outlast = np.where(
            pd.isna(df_aircraft_shaved_tasks['LAST EXEC DT']) == False)[0]
        df_aircraft_shaved_tasks['LAST EXEC DT'] = df_aircraft_shaved_tasks['LAST EXEC DT'].fillna(
            df_aircraft_shaved_tasks['LIMIT EXEC DT'])
        df_aircraft_shaved_tasks['LAST EXEC FC'] = df_aircraft_shaved_tasks['LAST EXEC FC'].fillna(
            df_aircraft_shaved_tasks['LIMIT FC'])
        df_aircraft_shaved_tasks['LAST EXEC FH'] = df_aircraft_shaved_tasks['LAST EXEC FH'].fillna(
            df_aircraft_shaved_tasks['LIMIT FH'])

        return df_aircraft_shaved_tasks, FH_outlast, FC_outlast, DT_outlast, last_executed

    def simulate_lifetime(self, aircraft):
        #### SET 3: Simulation lifetime ####
        # Consists of the following rows: 0 = date (integer value), 1 = FH sim, 2 = FC sim, 3 = month sim, 4 = day sim
        # simulation reqired to get up-to-date due dates!
        dfh = self.aircraft_info[aircraft]['DFH']
        dfc = self.aircraft_info[aircraft]['DFC']
        index_ac = np.where(self.delivery['A/C TAIL'] == aircraft)[0][0]
        delivery_date = self.delivery['DELIVERY DATE'][index_ac].date()

        end_date = integer_to_datetime(20690101)
        # end_date = advance_date(delivery_date, years=50)
        date_range = pd.date_range(delivery_date, end_date)

        simulated_lifetime = np.zeros((7, len(date_range)))

        simulated_lifetime[0, :] = np.array(datetime_to_integer(date_range))
        a_checks_dates = list(self.final_fleet_schedule['A'][aircraft].keys())
        c_checks_dates = list(self.final_fleet_schedule['C'][aircraft].keys())
        c_checks_dates_end = []

        for c_check_date in c_checks_dates:
            real_tat = self.final_fleet_schedule['C'][aircraft][c_check_date]['TAT']
            c_checks_dates_end.append(
                advance_date(c_check_date, days=real_tat))

        fh, fc = 0, 0

        day = integer_to_datetime(int(simulated_lifetime[0, 0]))
        if day.day == 1:
            month_th = -1
        else:
            month_th = 0

        for _ in range(len(date_range)):
            day = integer_to_datetime(int(simulated_lifetime[0, _]))
            # TODO this is kinda nonsense from airline
            if day.day == 1:
                month_th += 1
                simulated_lifetime[6, _] = month_th
            else:
                simulated_lifetime[6, _] = month_th

            if day in a_checks_dates:
                simulated_lifetime[4, _] = 1

            for k in range(len(c_checks_dates)):
                if c_checks_dates[k] <= day <= c_checks_dates_end[k]:
                    simulated_lifetime[5, _] = 1

            if simulated_lifetime[4, _] or simulated_lifetime[5, _]:
                simulated_lifetime[1, _] = np.round(fh, decimals=2)
                simulated_lifetime[2, _] = np.round(fc, decimals=2)

            else:
                month = (day.month_name()[0:3]).upper()
                fh = fh + dfh[month]
                fc = fc + dfc[month]
                simulated_lifetime[1, _] = np.round(fh, decimals=2)
                simulated_lifetime[2, _] = np.round(fc, decimals=2)

        simulated_lifetime[3, :] = range(1, len(date_range) + 1)
        # if aircraft == 'Aircraft-2':
        #     import ipdb
        #     ipdb.set_trace()
        return simulated_lifetime, a_checks_dates, c_checks_dates, c_checks_dates_end


class TaskBin:
    def __init__(self, dates, skills, fill_ratio):
        self.dates = dates

        pass

    # merges 2 bins and outputs a bin
    @staticmethod
    def merge_bins():
        pass

    # mostly for c_checks
    @staticmethod
    def order_bins():
        pass
