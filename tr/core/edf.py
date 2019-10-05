import numpy
import pandas as pd
from tqdm import tqdm
import pulp as plp
import time
import operator
# from copy import deep

from collections import OrderedDict, defaultdict

# from tr.core.resources import f1_in, f2_out
from tr.core.parsers import excel_to_book, book_to_kwargs
from tr.core.common import FleetManagerBase
from tr.core.utils import advance_date, dates_between, save_pickle, load_pickle
from tr.core.utils import convert_iso_to_timestamp
from tr.core.csp import Variable, Assignment, Schedule
from tr.core.backtrack import solve_csp_schedule, check_feasibility, csp_lowest_cardinalities
from tr.core.backtrack import csp_lowest_cardinalities, all_unique_domains
from tr.core.tree_search import TreeDaysPlanner
from tr.core.tasks_planner import TasksPlanner

checks = {
    'A_INITIAL': {
        'initial-days': 'DY-A',
        'initial-hours': 'FH-A',
        'initial-cycles': 'FC-A',
        'max-days': 'A-CI-DY',
        'max-hours': 'A-CI-FH',
        'max-cycles': 'A-CI-FC'
    }
}


class SchedulerEDF(FleetManagerBase):
    """ Currently for A/C-Checks only, nodes are partial schedules and, 
    tree as total schedules """
    def __init__(self, *args, **kwargs):
        FleetManagerBase.__init__(self, **kwargs)
        self.full_tree = []
        self.initial_context = self._compute_inital_context()
        self.global_schedule = self._set_global_schedule()
        # self.restrict_calendar_c_checks()
        # self.calendar.calendar[c_check_date]['allowed']['a-type']= False

        iso_str = '01/10/2020'
        daterinos = pd.to_datetime(iso_str, format='%m/%d/%Y')
        self.calendar.calendar[daterinos]['resources']['slots']['a-type'] += 1

        # self.plan_by_days()

        # self.plan_maintenance_opportunities()
        # save_pickle(self.global_schedule, "checks.pkl")
        # self.global_schedule = load_pickle('checks.pkl')

        # self.pre_process_tasks()
        # save_pickle(self.aircraft_tasks, 'aircraft_tasks_processed.pkl')
        # self.aircraft_tasks = load_pickle('aircraft_tasks_processed.pkl')
        self.plan_tasks_fleet()

        # self.save_checks_to_xlsx()
        # self.save_tasks_to_xlsx()

    def plan_by_days(self):
        calendar = self.calendar
        fleet = self.fleet
        self.optimizer = TreeDaysPlanner(calendar, fleet)
        all_schedules = self.optimizer.solve_schedule()

    def _set_global_schedule(self):
        global_schedule = OrderedDict()
        for aircraft in self.initial_context.keys():
            global_schedule[aircraft] = {}
            # if aircraft in self.kwargs_c_checks.keys():
            #     global_schedule[aircraft].update(
            #         {'c_checks': self.kwargs_c_checks[aircraft]})
            #     global_schedule[aircraft].update(
            #         {'c_check_days': self.kwargs_c_checks_days[aircraft]})

            global_schedule[aircraft]['last_due_dates'] = []
            global_schedule[aircraft]['assigned_dates'] = []
            global_schedule[aircraft]['due_dates'] = []
            global_schedule[aircraft]['DY'] = []
            global_schedule[aircraft]['FH'] = []
            global_schedule[aircraft]['FC'] = []
            global_schedule[aircraft]['DY LOST'] = []
            global_schedule[aircraft]['FH LOST'] = []
            global_schedule[aircraft]['FC LOST'] = []
        return global_schedule

    def save_checks_to_xlsx(self):
        print("INFO: Saving xlsx files")
        dict1 = OrderedDict()
        dict1['Fleet'] = []
        dict1['A/C ID'] = []
        dict1['START'] = []
        dict1['END'] = []
        dict1['DY'] = []
        dict1['FH'] = []
        dict1['FC'] = []
        dict1['DY LOST'] = []
        dict1['FH LOST'] = []
        dict1['FC LOST'] = []
        for aircraft in self.global_schedule.keys():
            for _ in range(len(self.global_schedule[aircraft]['due_dates'])):
                dict1['Fleet'].append(aircraft[0:4])
                dict1['A/C ID'].append(aircraft[5:])
                dict1['START'].append(
                    self.global_schedule[aircraft]['due_dates'][_].date().isoformat())
                dict1['END'].append(
                    self.global_schedule[aircraft]['due_dates'][_].date().isoformat())
                dict1['DY'].append(self.global_schedule[aircraft]['DY'][_])
                dict1['FH'].append(self.global_schedule[aircraft]['FH'][_])
                dict1['FC'].append(self.global_schedule[aircraft]['FC'][_])
                dict1['DY LOST'].append(self.global_schedule[aircraft]['DY LOST'][_])
                dict1['FH LOST'].append(self.global_schedule[aircraft]['FH LOST'][_])
                dict1['FC LOST'].append(self.global_schedule[aircraft]['FC LOST'][_])
        df = pd.DataFrame(dict1, columns=dict1.keys())

        print(df)
        df.to_excel('checks.xlsx')

    def save_tasks_to_xlsx(self):
        print("INFO: Saving xlsx files")
        dict1 = OrderedDict()
        dict1['A/C ID'] = []
        dict1['MAINTENANCE OPPORTUNITY'] = []
        dict1['ITEM'] = []
        dict1['REF TAP'] = []
        dict1['DESCRIPTION'] = []
        dict1['BLOCK'] = []
        dict1['SKILL'] = []
        dict1['TASK BY BLOCK'] = []

        df = self.df_tasks
        for aircraft in tqdm(self.global_schedule_tasks.keys()):
            for day in self.global_schedule_tasks[aircraft]['a_check_tasks'].keys():
                for item in self.global_schedule_tasks[aircraft]['a_check_tasks'][day]:
                    item_idxs = df[(df['A/C'] == aircraft)
                                   & (df['ITEM'] == item)].index.values.astype(int)
                    # item_idxs = item_idxs.tolist()
                    assert len(item_idxs) != 0
                    refs = df['REF TAP'][item_idxs].tolist()
                    descriptions = df['DESCRIPTION'][item_idxs].tolist()
                    blocks = df['BLOCK'][item_idxs].tolist()
                    skills = df['SKILL'][item_idxs].tolist()
                    taskbblock = df['TASK BY BLOCK'][item_idxs].tolist()
                    for _ in range(len(refs)):
                        dict1['A/C ID'].append(aircraft)
                        dict1['MAINTENANCE OPPORTUNITY'].append(day.date().isoformat())
                        dict1['ITEM'].append(item)
                        dict1['REF TAP'].append(refs[_])
                        dict1['DESCRIPTION'].append(descriptions[_])
                        dict1['BLOCK'].append(blocks[_])
                        dict1['SKILL'].append(skills[_])
                        dict1['TASK BY BLOCK'].append(taskbblock[_])

                # dict1['A/C ID'].append(aircraft)
                # dict1['START'].append(self.global_schedule_tasks[aircraft]['due_dates']
                #                       [_].date().isoformat())
                # dict1['END'].append(self.global_schedule_tasks[aircraft]['due_dates']
                #                     [_].date().isoformat())

        df = pd.DataFrame(dict1, columns=dict1.keys())

        len(df)
        df.to_excel('tasks.xlsx')

    def save_checks_pickle(self, filename="checks.pkl"):
        print("INFO: compressing checks information")
        save_pickle(self.global_schedule, filename)

    def load_checks_pickle(self, filename="checks.pkl"):
        print("INFO: loading compressed checks information")
        self.global_schedule = load_pickle(filename)

    def save_tasks_pickle(self, filename="tasks.pkl"):
        print("INFO: compressing tasks information")
        save_pickle(self.global_schedule_tasks, filename)

    def load_checks_pickle(filename="tasks.pkl"):
        print("INFO: loading compressed tasks information")
        self.global_schedule_tasks = load_pickle(filename)

    def _add_to_global_schedule(self, schedule_partial):
        for aircraft in self.fleet.aircraft_info.keys():

            self.global_schedule[aircraft]['last_due_dates'].append(
                schedule_partial[aircraft]['A_INITIAL']['last_due_date'])
            self.global_schedule[aircraft]['assigned_dates'].append(
                schedule_partial[aircraft]['A_INITIAL']['assigned_date'])
            self.global_schedule[aircraft]['due_dates'].append(
                schedule_partial[aircraft]['A_INITIAL']['due_date'])

            self.global_schedule[aircraft]['DY'].append(
                schedule_partial[aircraft]['A_INITIAL']['DY'])
            self.global_schedule[aircraft]['FH'].append(
                schedule_partial[aircraft]['A_INITIAL']['FH'])
            self.global_schedule[aircraft]['FC'].append(
                schedule_partial[aircraft]['A_INITIAL']['FC'])
            self.global_schedule[aircraft]['DY LOST'].append(
                schedule_partial[aircraft]['A_INITIAL']['DY LOST'])
            self.global_schedule[aircraft]['FH LOST'].append(
                schedule_partial[aircraft]['A_INITIAL']['FH LOST'])
            self.global_schedule[aircraft]['FC LOST'].append(
                schedule_partial[aircraft]['A_INITIAL']['FC LOST'])

    def plan_maintenance_opportunities(self):
        time0 = time.time()
        context = self.initial_context
        problematic_date = convert_iso_to_timestamp('06/02/2021')

        counter = 0
        last_due_date = convert_iso_to_timestamp('06/02/2020')
        while not self.is_context_done(context):
            csp_vars = self.cspify(context)
            if last_due_date == problematic_date:
                # a_checks_one = csp_lowest_cardinalities(csp_vars)
                a_checks_one = all_unique_domains(csp_vars)

                self.add_a_checks(a_checks_one)

                import ipdb
                ipdb.set_trace()
                csp_vars = self.cspify(context)
                crucial = convert_iso_to_timestamp('12/18/2020')
                csp_vars.vars_domain['Aircraft-16'].append(crucial)
                csp_vars.vars_domain['Aircraft-29'].append(crucial)
                import ipdb
                ipdb.set_trace()

            # import ipdb
            # ipdb.set_trace()
            # assert check_just_ones(csp_vars)
            try:
                assignment, tree = solve_csp_schedule(csp_vars)
            except:
                import ipdb
                ipdb.set_trace()
            self.full_tree.append(tree)
            assignment_dict = assignment.assignment
            self.restrict_calendar(assignment_dict)

            last_due_date = assignment_dict[list(assignment_dict.keys())[0]]

            print("INFO: planned until {}".format(last_due_date))
            print("INFO: Elapsed time (minutes): {}".format((time.time() - time0) / 60))
            schedule_partial = self.get_schedule_stats(assignment_dict, context)

            self._add_to_global_schedule(schedule_partial)
            context = self.compute_next_context(schedule_partial, self.end_date)
            counter += 1
        print("INFO: Finished planning maintenance opportunities")

    def add_a_checks(self, a_checks_one):

        # '2020-12-18 00:00:00'
        # problematic_date = convert_iso_to_timestamp('06/02/2021')

        crucial = convert_iso_to_timestamp('12/18/2020')

        # for _ in a_checks_one:
        #     self.calendar.calendar[_]['resources']['slots']['a-type'] += 5

        self.calendar.calendar[crucial]['resources']['slots']['a-type'] += 1

    def restrict_calendar_c_checks(self):
        for aircraft in self.global_schedule.keys():
            if 'c_checks' in self.global_schedule[aircraft].keys():
                for c_check_code in self.global_schedule[aircraft]['c_checks'].keys():
                    for c_check_date in self.global_schedule[aircraft]['c_checks'][c_check_code]:
                        self.calendar.calendar[c_check_date]['resources']['slots']['c-type'] -= 1
                        # print(self.calendar.calendar[c_check_date]['allowed']['a-type'])
                        # import ipdb; ipdb.set_trace()
                        # self.calendar.calendar[c_check_date]['allowed']['a-type']= False

    def restrict_calendar(self, assignment):
        check_types = ['a-type', 'c-type']
        for aircraft in assignment.keys():
            due_date = assignment[aircraft]
            for _ in check_types:
                self.calendar.calendar[due_date]['resources']['slots'][_] -= 1

    def cspify(self, context, least_domain_ordering=False):
        # order vars by due date
        sorted_x = sorted(context.items(),
                          key=lambda kv: kv[1]['A_INITIAL']['due_date'].timestamp(),
                          reverse=True)
        variables = OrderedDict(sorted_x)

        vars_domain = OrderedDict()
        for variable in variables:
            start_date = variables[variable]['A_INITIAL']['assigned_date']
            end_date = variables[variable]['A_INITIAL']['due_date']
            domain = self.get_domain(start_date, end_date, variable=variable)
            vars_domain[variable] = domain

        if least_domain_ordering:
            # import ipdb; ipdb.set_trace()
            sorted_least_domain = sorted(vars_domain.items(), key=lambda k: len(k[1]), reverse=True)
            least_domain = OrderedDict(sorted_least_domain)
            ordered_least_domain_vars = []
            for variable in variables:
                domain = least_domain[variable]
                var = Variable(name=variable, domain=domain)
                ordered_least_domain_vars.append(var)
            assignment = Assignment(ordered_least_domain_vars)
            # import ipdb; ipdb.set_trace()
        else:
            ordered_due_date_vars = []
            for variable in variables:
                domain = vars_domain[variable]
                var = Variable(name=variable, domain=domain)
                ordered_due_date_vars.append(var)
            assignment = Assignment(ordered_due_date_vars)
            # import ipdb; ipdb.set_trace()

        return assignment

    def get_max_slots(self, due_date, key=None):
        check_types = ['a-type', 'c-type']
        slots = [
            self.calendar.calendar[due_date]['resources']['slots'][check] for check in check_types
        ]
        max_slots = max(slots)
        return max_slots

    def get_domain(self, date_start, date_end, check_type='a-type', variable=None):
        if 'c_check_days' in self.global_schedule[variable].keys():
            if date_end in self.global_schedule[variable]['c_check_days']:
                # import ipdb;
                # ipdb.set_trace()
                for code in self.global_schedule[variable]['c_checks'].keys():
                    if date_end in self.global_schedule[variable]['c_checks'][code]:
                        domain = list(self.global_schedule[variable]['c_checks'][code])[-1]
                        # import ipdb;
                        # ipdb.set_trace()
                        return [domain]

        domain = []
        domain.append(date_start)
        due_date = date_start
        while due_date <= date_end:
            if self.calendar.calendar[due_date]['allowed'][
                    'public holidays'] and self.calendar.calendar[due_date]['allowed']['a-type']:
                for _ in range(self.get_max_slots(due_date, variable)):
                    domain.append(due_date)
            due_date = advance_date(due_date, days=int(1))
        assert len(domain) != 0

        return domain

    def is_context_done(self, context):
        for aircraft in context.keys():
            if context[aircraft]['A_INITIAL']['due_date'] > self.end_date:
                return True
        return False

    def get_schedule_stats(self, assignment, context):

        schedule_partial = OrderedDict()

        for aircraft in assignment.keys():
            schedule_partial[aircraft] = {}
            accumulated, waste = self.get_aircraft_stats(aircraft,
                                                         assignment,
                                                         context,
                                                         check_type='a-type')
            schedule_partial[aircraft]['A_INITIAL'] = {}
            schedule_partial[aircraft]['A_INITIAL']['last_due_date'] = context[aircraft][
                'A_INITIAL']['last_due_date']
            schedule_partial[aircraft]['A_INITIAL']['due_date'] = context[aircraft]['A_INITIAL'][
                'due_date']
            schedule_partial[aircraft]['A_INITIAL']['assigned_date'] = assignment[aircraft]
            schedule_partial[aircraft]['A_INITIAL']['DY'] = accumulated[0]
            schedule_partial[aircraft]['A_INITIAL']['FH'] = accumulated[1]
            schedule_partial[aircraft]['A_INITIAL']['FC'] = accumulated[2]
            schedule_partial[aircraft]['A_INITIAL']['DY LOST'] = waste[0]
            schedule_partial[aircraft]['A_INITIAL']['FH LOST'] = waste[1]
            schedule_partial[aircraft]['A_INITIAL']['FC LOST'] = waste[2]

        return schedule_partial

    def get_aircraft_stats(self, aircraft, assignment, context, check_type='a-type'):

        maxDY = self.fleet.aircraft_info[aircraft]['A_INITIAL'][checks['A_INITIAL']['max-days']]
        maxFH = self.fleet.aircraft_info[aircraft]['A_INITIAL'][checks['A_INITIAL']['max-hours']]
        maxFC = self.fleet.aircraft_info[aircraft]['A_INITIAL'][checks['A_INITIAL']['max-cycles']]

        waste_due_date = context[aircraft]['A_INITIAL']['waste']
        assigned_date = assignment[aircraft]
        due_date = context[aircraft]['A_INITIAL']['due_date']
        accumulated = [0, 0, 0]
        # waste = [0, 0, 0]
        while due_date >= assigned_date:
            month = (due_date.month_name()[0:3]).upper()
            due_date = advance_date(due_date, days=int(-1))
            waste_due_date[0] += 1
            waste_due_date[1] += self.fleet.aircraft_info[aircraft]['DFH'][month]
            waste_due_date[2] += self.fleet.aircraft_info[aircraft]['DFC'][month]

        accumulated[0] = maxDY - waste_due_date[0]
        accumulated[1] = maxFH - waste_due_date[1]
        accumulated[2] = maxFC - waste_due_date[2]
        return accumulated, waste_due_date

    def fill_in_calendar(self, calendar, aircraft, context_aircraft, check_type='a-type'):

        due_date = context_aircraft['due_date']
        waste = context_aircraft['waste']
        last_due_date = context_aircraft['last_due_date']
        while due_date >= last_due_date:
            if calendar[due_date]['allowed']['public holidays'] and calendar[due_date]['allowed'][
                    'a-type']:
                if calendar[due_date]['resources']['slots'][check_type] >= 0:
                    calendar[due_date]['resources']['slots'][check_type] -= 1
                    context_aircraft['due_date'] = due_date
                    context_aircraft['waste'] = waste
                    return calendar, context_aircraft
                else:
                    month = due_date.month_name()[0:3]
                    due_date = advance_date(due_date, days=int(-1))
                    waste[0] += 1
                    waste[1] += self.fleet.aircraft_info[aircraft]['DFH'][month]
                    waste[2] += self.fleet.aircraft_info[aircraft]['DFC'][month]
            else:
                month = due_date.month_name()[0:3]
                due_date = advance_date(due_date, days=int(-1))
                waste[0] += 1
                waste[1] += self.fleet.aircraft_info[aircraft]['DFH'][month]
                waste[2] += self.fleet.aircraft_info[aircraft]['DFC'][month]

        print("ERROR: IMPOSSIBLE SCHEDULE")
        return calendar, 'IMPOSSIBLE'

    def _compute_inital_context(self):
        due_dates = OrderedDict()
        for check in checks.keys():
            for aircraft in self.fleet.aircraft_info.keys():
                DY_i = self.fleet.aircraft_info[aircraft][check][checks[check]['initial-days']]
                FH_i = self.fleet.aircraft_info[aircraft][check][checks[check]['initial-hours']]
                FC_i = self.fleet.aircraft_info[aircraft][check][checks[check]['initial-cycles']]
                maxDY = self.fleet.aircraft_info[aircraft][check][checks[check]['max-days']]
                maxFH = self.fleet.aircraft_info[aircraft][check][checks[check]['max-hours']]
                maxFC = self.fleet.aircraft_info[aircraft][check][checks[check]['max-cycles']]
                due_dates[aircraft] = {}
                due_dates[aircraft][check] = {}
                due_dates[aircraft][check]['assigned_date'] = self.start_date
                due_dates[aircraft][check]['due_date'], due_dates[aircraft][check][
                    'waste'], due_dates[aircraft][check][
                        'last_due_date'] = self.compute_next_due_date(self.start_date,
                                                                      self.end_date,
                                                                      aircraft,
                                                                      DY_i=DY_i,
                                                                      FH_i=FH_i,
                                                                      FC_i=FC_i,
                                                                      maxDY=maxDY,
                                                                      maxFH=maxFH,
                                                                      maxFC=maxFC)

        return due_dates

    def compute_next_context(self, schedule_partial, end_date, check_type='A_INITIAL'):
        """ Given start_due_dates for all the fleet, and an end_date, assign a schedule
        this is similar to solving a MILP  """
        for check in checks.keys():
            for aircraft in schedule_partial.keys():
                maxDY = self.fleet.aircraft_info[aircraft][check][checks[check]['max-days']]
                maxFH = self.fleet.aircraft_info[aircraft][check][checks[check]['max-hours']]
                maxFC = self.fleet.aircraft_info[aircraft][check][checks[check]['max-cycles']]
                schedule_partial[aircraft][check]['due_date'], schedule_partial[aircraft][check][
                    'waste'], schedule_partial[aircraft][check][
                        'last_due_date'] = self.compute_next_due_date(
                            schedule_partial[aircraft]['A_INITIAL']['assigned_date'],
                            end_date,
                            aircraft,
                            maxDY=maxDY,
                            maxFH=maxFH,
                            maxFC=maxFC)
        return schedule_partial  # this is the context, e.g, next_due_dates

    def compute_next_due_date(self,
                              start_date,
                              end_date,
                              aircraft,
                              DY_i=0,
                              FH_i=0,
                              FC_i=0,
                              maxDY=0,
                              maxFH=0,
                              maxFC=0):
        DY, FH, FC = DY_i, FH_i, FC_i

        due_date = start_date
        month = (start_date.month_name()[0:3]).upper()
        maxDY_proxy = maxDY - 1
        maxFH_proxy = maxFH - self.fleet.aircraft_info[aircraft]['DFH'][month]
        maxFC_proxy = maxFC - self.fleet.aircraft_info[aircraft]['DFC'][month]

        while DY < maxDY_proxy and FH < maxFH_proxy and FC < maxFC_proxy:
            month = (due_date.month_name()[0:3]).upper()
            DY += 1
            FH += self.fleet.aircraft_info[aircraft]['DFH'][month]
            FC += self.fleet.aircraft_info[aircraft]['DFC'][month]
            self.fleet.aircraft_info[aircraft]['DFH'][month]

            due_date = advance_date(due_date, days=int(1))

        waste = [maxDY - DY, maxFH - FH, maxFC - FC]
        return due_date, waste, start_date


###############################################################################
# TASKS
###############################################################################

    def pre_process_tasks(self):
        print("INFO: Pre processing tasks")
        for aircraft in tqdm(self.aircraft_tasks.keys()):
            self._extend_process_a_tasks(aircraft)
        print("INFO: tasks information processed and ready to use")

    def _extend_process_a_tasks(self, aircraft):

        print("INFO: Extend processing tasks A/C: {}".format(aircraft))
        a_items_codes = self.aircraft_tasks[aircraft]['a_checks_items']
        black_list = []
        for a_item_code in a_items_codes:
            a_item = self.aircraft_tasks[aircraft][a_item_code]
            task_number = list(a_item.keys())[-1]
            task_a = a_item[task_number]
            last_exec_date = task_a['LAST EXEC DT'] if task_a['LAST EXEC DT'] else task_a[
                'LIMIT EXEC DT']
            last_exec_fc = task_a['LAST EXEC FC'] if task_a['LAST EXEC FC'] else task_a['LIMIT FC']
            last_exec_fh = task_a['LAST EXEC FH'] if task_a['LAST EXEC FH'] else task_a['LIMIT FH']

            if not (last_exec_date and (last_exec_fc or last_exec_fh)):
                # print("WARNING: Task {} ignored, missing values".format(
                #     a_item_code))
                black_list.append(a_item_code)
                continue
            elif task_a['LIMIT FH'] == 2000:
                # print(
                # "WARNING: Task {} ignored, incorrect LIMIT FH=2000".format(
                #     a_item_code))
                black_list.append(a_item_code)
                continue
            elif (not task_a['PER FC'] and not task_a['PER FH']):
                black_list.append(a_item_code)

            # assert last_exec_date and (last_exec_fc
            #                            or last_exec_fh), "shit excel"

            maxFC_task = task_a['LIMIT FC'] if task_a['LIMIT FC'] else 1000000
            maxFH_task = task_a['LIMIT FH'] if task_a['LIMIT FH'] else 1000000
            current_date = last_exec_date
            current_FC, current_FH, days = 0, 0, 0

            if last_exec_date < self.start_date:
                days_passed = dates_between(last_exec_date, self.start_date)
                current_FC = last_exec_fc + current_FC
                current_FH = last_exec_fh + current_FH

            else:
                days_passed = 0
                current_date = last_exec_date

            while days < days_passed:
                month = (current_date.month_name()[0:3]).upper()
                current_FH += self.fleet.aircraft_info[aircraft]['DFH'][month]
                current_FC += self.fleet.aircraft_info[aircraft]['DFC'][month]
                days += 1
                current_date = advance_date(current_date, days=int(1))

            due_date = current_date
            while due_date < last_exec_date and current_FC < maxFH_task and current_FC < maxFC_task:
                month = (due_date.month_name()[0:3]).upper()
                current_FH += self.fleet.aircraft_info[aircraft]['DFH'][month]
                current_FC += self.fleet.aircraft_info[aircraft]['DFC'][month]
                days += 1
                due_date = advance_date(due_date, days=int(1))

            try:
                assert due_date >= current_date
                # assert current_FC < (maxFC_task + 500), "Task {} on due_date".format(
                #     a_item_code) # +500 because of '534160-02-3'
                # assert current_FH < (
                #     maxFH_task + 1000), "Task {} on due_date".format(
                #         a_item_code)  # +300 because '532164-01-6' and +1000
                # because of '253400-01-1'
                # assert current_date == self.start_date, "current date error"
            except:
                import ipdb
                ipdb.set_trace()
            self.aircraft_tasks[aircraft][a_item_code][task_number].update({
                'LIMIT FC': maxFC_task,
                'LIMIT FH': maxFH_task,
                'LAST EXEC DT': last_exec_date,
                'LAST EXEC FC': last_exec_fc,
                'LAST EXEC FH': last_exec_fh,
                'CURRENT FC': current_FC,
                'CURRENT FH': current_FH,
                'CURRENT DATE': current_date,
                'DUE DATE': due_date
            })

        for blacked in black_list:
            self.aircraft_tasks[aircraft]['a_checks_items'].remove(blacked)

    def plan_tasks_fleet(self):

        self.optimizer_tasks = TasksPlanner(self.aircraft_tasks, self.fleet.aircraft_info,
                                            self.df_tasks, self.skills, self.skills_ratios_A,
                                            self.skills_ratios_C, self.man_hours,
                                            self.delivery_date, self.df_aircraft_shaved)
        all_schedules = self.optimizer_tasks.solve_tasks()

        # global_schedule_tasks = OrderedDict()
        # print("INFO: Task planning for the fleet")
        # for aircraft in tqdm(self.global_schedule.keys()):
        #     schedule_tasks = self.plan_tasks(aircraft)
        #     global_schedule_tasks[aircraft] = schedule_tasks
        # self.global_schedule_tasks = global_schedule_tasks
        # print("INFO: Task Planning finished")

    def plan_tasks(self, aircraft):
        # A-checks only have flight hours for now
        schedule_tasks = OrderedDict()
        schedule_tasks['a_check_tasks'] = self.plan_a_checks(aircraft)
        return schedule_tasks

    def plan_a_checks(self, aircraft):
        a_items_codes = self.aircraft_tasks[aircraft]['a_checks_items']
        assigned_dates = self.global_schedule[aircraft]['assigned_dates']
        a_checks_tasks_schedule = OrderedDict()
        for _ in assigned_dates:
            a_checks_tasks_schedule[_] = []
        counter = 1
        # starts on the second hangar day
        # if the due date is before the second hangar day, put it on the first
        # hangar day
        for _ in range(len(assigned_dates) - 1):
            for a_item_code in a_items_codes:
                a_item = self.aircraft_tasks[aircraft][a_item_code]
                task_number = list(a_item.keys())[-1]
                task_a = a_item[task_number]
                if task_a['DUE DATE'] < assigned_dates[counter]:
                    hangar_day = assigned_dates[_]
                    a_checks_tasks_schedule[hangar_day].append(a_item_code)
                    self.move_due_date_item(task_a, aircraft, assigned_dates[counter], task_number,
                                            a_item_code)
                    # try:
                    #     if counter > 1:
                    #         assert (task_a['DUE DATE'] <
                    #                 assigned_dates[counter - 1])
                    # except:
                    #     print("yayikers bro")
                    #     import ipdb
                    #     ipdb.set_trace()
            counter += 1

            # returns days of checks to tasks
        return a_checks_tasks_schedule

    def move_due_date_item(self, task_a, aircraft, assigned_date, task_number, a_item_code):

        delta_FC = task_a['PER FC'] if task_a['PER FC'] else 100000
        delta_FH = task_a['PER FH'] if task_a['PER FH'] else 100000
        current_FC, current_FH = 0, 0

        due_date = assigned_date
        month = (due_date.month_name()[0:3]).upper()
        dfh = self.fleet.aircraft_info[aircraft]['DFH'][month]
        dfc = self.fleet.aircraft_info[aircraft]['DFC'][month]
        # current_FH += self.fleet.aircraft_info[aircraft]['DFH'][month]
        # current_FC += self.fleet.aircraft_info[aircraft]['DFC'][month]

        days = round(min(delta_FC / dfc, delta_FH / dfh))
        due_date = advance_date(due_date, days=int(days))

        # while current_FC < delta_FC and current_FC < delta_FH:
        #     month = (due_date.month_name()[0:3]).upper()
        #     current_FH += self.fleet.aircraft_info[aircraft]['DFH'][month]
        #     current_FC += self.fleet.aircraft_info[aircraft]['DFC'][month]
        #     due_date = advance_date(due_date, days=int(1))

        self.aircraft_tasks[aircraft][a_item_code]['assignments'].append(assigned_date)
        self.aircraft_tasks[aircraft][a_item_code][task_number]['DUE DATE'] = due_date

if __name__ == '__main__':

    import time
    from resources import f1_in_checks, f1_in_tasks, f2_out

    t = time.time()
    try:
        book_checks = excel_to_book(f1_in_checks)
        book_tasks, book_output = 0, 0
        # book_tasks = excel_to_book(f1_in_tasks)
        # book_output = excel_to_book(f2_out)
    except Exception as e:
        raise e

    kwargs = book_to_kwargs(book_checks, book_tasks, book_output)
    scheduler = SchedulerEDF(**kwargs)
    print("INFO: total elapsed time {} seconds".format(time.time() - t))
