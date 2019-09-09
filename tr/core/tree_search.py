import treelib
import pandas as pd

from treelib import Tree
from tqdm import tqdm
from collections import OrderedDict, deque
from copy import deepcopy
from functools import partial

from tr.core.tree_utils import build_fleet_state, order_fleet_state
from tr.core.tree_utils import NodeScheduleDays, generate_code, valid_calendar
from tr.core.tree_utils import fleet_operate_A, fleet_operate_C
from tr.core.tree_utils import generate_D_check_code

from tr.core.utils import advance_date, save_pickle, load_pickle

maintenance_actions = [1, 0]  # the order of this list reflects an heuristc btw
type_checks = ['A', 'C']  # type of checks

import sys
sys.setrecursionlimit(1500)  #all hope is lost....


class TreeDaysPlanner:
    def __init__(self, calendar, fleet):
        self.calendar = calendar
        self.fleet = fleet
        self.calendar_tree = {'A': Tree(), 'C': Tree()}
        iso_str = '1/1/2022'
        self.daterinos = pd.to_datetime(iso_str, format='%m/%d/%Y')
        self.removed_aircrafts = OrderedDict()
        # self.final_schedule = {'A': {}, 'C': {}}
        import ipdb
        ipdb.set_trace()
        try:
            self.phased_out = load_pickle("phased_out")
            self.final_calendar = load_pickle("C_checks.pkl")
        except:
            self.phased_out = OrderedDict()
            self.final_calendar = {'A': {}, 'C': {}}

        try:
            metrics_dict = load_pickle("metrics_dict")
            self.metrics(metrics_dict)
        except:
            pass


        self.utilization_ratio, self.code_generator, self.tats, self.finale_schedule = \
            self.__build_calendar_helpers()

        # self.daterinos_start = valid_calendar(self.calendar)

        for type_check in type_checks:
            fleet_state = build_fleet_state(self.fleet, type_check=type_check)
            fleet_state = order_fleet_state(fleet_state)

            root = NodeScheduleDays(calendar=OrderedDict(),
                                    day=self.calendar.start_date,
                                    fleet_state=fleet_state,
                                    action_maintenance=0,
                                    assignment=[],
                                    tag="Root",
                                    identifier="root")

            self.calendar_tree[type_check].add_node(root)

        self.schedule_counter = 0
        self.all_schedules = deque(maxlen=100)  # maintain only the top 10

    def __build_calendar_helpers(self):
        fleet_state = build_fleet_state(self.fleet, type_check='C')
        code_generator = {
            'A': partial(generate_code, 4),
            'C': partial(generate_code, 12)
        }
        utilization_ratio = OrderedDict()
        tats = OrderedDict()
        finale_schedule = OrderedDict()
        for _ in self.fleet.aircraft_info.keys():
            utilization_ratio[_] = {}
            finale_schedule[_] = {}
            utilization_ratio[_]['DFH'] = self.fleet.aircraft_info[_]['DFH']
            utilization_ratio[_]['DFC'] = self.fleet.aircraft_info[_]['DFC']

            c_elapsed_time = self.fleet.aircraft_info[_]['C_ELAPSED_TIME']
            c_elapsed_tats = list(c_elapsed_time.keys())
            c_elapsed_tats.remove('Fleet')
            new_code = fleet_state[_]['C-SN']
            tats[_] = {}  # code to tat
            for tat in c_elapsed_tats:
                new_code = code_generator['C'](new_code)
                tats[_][new_code] = c_elapsed_time[tat]

        return utilization_ratio, code_generator, tats, finale_schedule

    # exceptions is a list of aircrafts that is in maintenance, thus not operating
    def fleet_operate_one_day(self,
                              fleet_state,
                              date,
                              on_maintenance=[],
                              type_check='A',
                              on_c_maintenance=[],
                              type_D_check=False):
        kwargs = {
            'fleet_state': fleet_state,
            'date': date,
            'on_maintenance': on_maintenance,
            'type_check': type_check,
            'on_c_maintenance': on_c_maintenance,
            'utilization_ratio': self.utilization_ratio,
            'code_generator': self.code_generator
        }
        if type_check == 'A':
            fleet_state = fleet_operate_A(**kwargs)
        elif type_check == 'C':
            kwargs['type_D_check'] = type_D_check
            fleet_state = fleet_operate_C(**kwargs)
        return fleet_state

    def check_safety_fleet(self, fleet_state):
        for key in fleet_state.keys():
            if fleet_state[key]['TOTAL-RATIO'] >= 1:
                return False
        return True

    def check_solved(self, current_calendar):
        if len(current_calendar) > 0:
            if list(current_calendar.keys())[-1] == self.daterinos:
                return True
            else:
                return False
        return False

    def get_slots(self, date, check_type):
        if check_type == 'A':
            slots = self.calendar.calendar[date]['resources']['slots'][
                'a-type']
        elif check_type == 'C':
            slots = self.calendar.calendar[date]['resources']['slots'][
                'c-type']
        return slots

    # there is no variables, just one bolean variable, do maintenance or not
    def expand_with_heuristic(self, node_schedule, type_check='A'):
        if type_check == 'A':
            childs = self.expand_a(node_schedule, type_check)
        elif type_check == 'C':
            childs = self.expand_c(node_schedule, type_check)
        return childs

    def expand_a(self, node_schedule, type_check):
        #recebe uma copia do calendario C para consultar
        # precisamos do mesmo que a outra a dizer merged
        calendar_0 = deepcopy(node_schedule.calendar)
        calendar_1 = deepcopy(node_schedule.calendar)
        fleet_state_0 = deepcopy(node_schedule.fleet_state)
        fleet_state_1 = deepcopy(node_schedule.fleet_state)
        on_c_maintenance_0 = deepcopy(node_schedule.on_c_maintenance)
        on_c_maintenance_1 = deepcopy(node_schedule.on_c_maintenance)
        on_c_maintenance_tats_0 = deepcopy(node_schedule.on_c_maintenance_tats)
        on_c_maintenance_tats_1 = deepcopy(node_schedule.on_c_maintenance_tats)
        on_maintenance_merged_0 = deepcopy(node_schedule.on_maintenance_merged)
        on_maintenance_merged_1 = deepcopy(node_schedule.on_maintenance_merged)

        day = node_schedule.day
        day_old = day
        childs = []
        day = advance_date(day, days=int(1))
        slots = self.get_slots(day, type_check)

        # if self.calendar_tree['A'].depth() == 123:
        #     import ipdb
        #     ipdb.set_trace()

        iso_str = '5/2/2019'
        daterinos = pd.to_datetime(iso_str, format='%m/%d/%Y')
        if day == daterinos:
            # import ipdb
            # ipdb.set_trace()
            slots += 1

        iso_str = '7/22/2019'
        daterinos = pd.to_datetime(iso_str, format='%m/%d/%Y')
        if day == daterinos:
            # import ipdb
            # ipdb.set_trace()
            slots += 1

        # slots = self.get_slots(day, type_check)

        # iso_str = '1/20/2020'
        # daterinos = pd.to_datetime(iso_str, format='%m/%d/%Y')
        # if day == daterinos:
        #     import ipdb
        #     ipdb.set_trace()
        #     slots += 1

        # iso_str = '12/03/2020'
        # daterinos = pd.to_datetime(iso_str, format='%m/%d/%Y')
        # if day == daterinos:
        #     import ipdb
        #     ipdb.set_trace()
        #     slots += 1

        # if self.calendar_tree['A'].depth() == 990:
        #     import ipdb
        #     ipdb.set_trace()

        #########################
        # we have
        ##################
        on_maintenance = list(fleet_state_1.keys())[0]
        ratio = fleet_state_0[on_maintenance]['TOTAL-RATIO']
        if self.calendar_tree['A'].depth() <= 239:
            maintenance_actions = [1, 0] if ratio > 0.78 else [0, 1]
        elif self.calendar_tree['A'].depth() <= 342:
            maintenance_actions = [1, 0] if ratio > 0.76 else [0, 1]
        elif self.calendar_tree['A'].depth() <= 726:
            maintenance_actions = [1, 0] if ratio > 0.76 else [0, 1]
        elif self.calendar_tree['A'].depth() <= 784:
            maintenance_actions = [1, 0] if ratio > 0.8 else [0, 1]
        elif self.calendar_tree['A'].depth() <= 926:
            maintenance_actions = [1, 0] if ratio > 0.8 else [0, 1]
        else:
            maintenance_actions = [1, 0] if ratio > 0.9 else [0, 1]

        # the real golden standard
        # on_maintenance = list(fleet_state_1.keys())[0]
        # ratio = fleet_state_0[on_maintenance]['TOTAL-RATIO']
        # if self.calendar_tree['A'].depth() <= 239:
        #     maintenance_actions = [1, 0] if ratio > 0.78 else [0, 1]
        # elif self.calendar_tree['A'].depth() <= 342:
        #     maintenance_actions = [1, 0] if ratio > 0.77 else [0, 1]
        # elif self.calendar_tree['A'].depth() <= 726:
        #     maintenance_actions = [1, 0] if ratio > 0.75 else [0, 1]
        # elif self.calendar_tree['A'].depth() <= 784:
        #     maintenance_actions = [1, 0] if ratio > 0.8 else [0, 1]
        # elif self.calendar_tree['A'].depth() <= 926:
        #     maintenance_actions = [1, 0] if ratio > 0.8 else [0, 1]
        # else:
        #     maintenance_actions = [1, 0] if ratio > 0.9 else [0, 1]

        for _ in self.phased_out.keys():
            if self.phased_out[_] == day:
                # import ipdb
                # ipdb.set_trace()
                fleet_state_0.pop(_, None)
                fleet_state_1.pop(_, None)

        on_c_maintenance_all = deepcopy(on_c_maintenance_0)
        for _ in on_c_maintenance_all:
            print("{}-{}".format(_, on_c_maintenance_tats_0[_]))
            if on_c_maintenance_tats_0[_] == 0:
                on_c_maintenance_0.remove(_)
                on_c_maintenance_tats_0.pop(_, None)
                on_c_maintenance_1.remove(_)
                on_c_maintenance_tats_1.pop(_, None)
                if _ in on_maintenance_merged_0:
                    on_maintenance_merged_0.remove(_)
                    on_maintenance_merged_1.remove(_)
            else:
                on_c_maintenance_tats_0[_] -= 1
                on_c_maintenance_tats_1[_] -= 1

        on_maintenance_merged = []
        if self.final_calendar['C'][day]['MAINTENANCE']:
            on_c_calendar = self.final_calendar['C'][day]['ASSIGNMENT']
            on_c_calendar_tat = self.final_calendar['C'][day][
                'ASSIGNED STATE']['TAT']
            on_c_maintenance_0.append(on_c_calendar)
            on_c_maintenance_1.append(on_c_calendar)
            on_c_maintenance_tats_0[on_c_calendar] = on_c_calendar_tat
            on_c_maintenance_tats_1[on_c_calendar] = on_c_calendar_tat
            if self.calendar_tree['A'].depth() <= 60:
                if fleet_state_0[on_c_calendar]['TOTAL-RATIO'] > 0.40:
                    if on_c_calendar not in on_maintenance_merged_0:
                        on_maintenance_merged.append(on_c_calendar)
            elif self.calendar_tree['A'].depth() <= 311:
                if fleet_state_0[on_c_calendar]['TOTAL-RATIO'] > 0.50:
                    if on_c_calendar not in on_maintenance_merged_0:
                        on_maintenance_merged.append(on_c_calendar)
            else:
                if fleet_state_0[on_c_calendar]['TOTAL-RATIO'] > 0.70:
                    if on_c_calendar not in on_maintenance_merged_0:
                        on_maintenance_merged.append(on_c_calendar)

        for action_value in maintenance_actions:
            if action_value and self.calendar.calendar[day]['allowed'][
                    'public holidays'] and self.calendar.calendar[day][
                        'allowed']['a-type']:

                on_maintenance = list(fleet_state_1.keys())[0:slots]
                # import ipdb
                # ipdb.set_trace()
                if slots == 2 and fleet_state_1[
                        on_maintenance[-1]]['FH-A'] <= 550:
                    on_maintenance = [list(fleet_state_1.keys())[0]]
                    import ipdb
                    ipdb.set_trace()

                for _ in on_maintenance_merged_0:
                    if _ in on_maintenance:
                        slots += 1
                        on_maintenance = list(fleet_state_1.keys())[0:slots]
                on_maintenance.extend(on_maintenance_merged)
                # if day == daterinos:
                #     import ipdb
                #     ipdb.set_trace()

                # for _ in self.removed_aircrafts:
                #     if _ in on_maintenance:
                #         slots += 1
                #         on_maintenance = list(fleet_state_1.keys())[0:slots]
                #         on_maintenance.remove(_)

                fleet_state_1 = self.fleet_operate_one_day(
                    fleet_state_1, day_old, on_maintenance, type_check,
                    on_c_maintenance_1)
                fleet_state_1 = order_fleet_state(fleet_state_1)

                valid = self.check_safety_fleet(fleet_state_1)
                if valid:
                    calendar_1[day] = {}
                    calendar_1[day]['SLOTS'] = slots
                    calendar_1[day]['MAINTENANCE'] = True
                    calendar_1[day]['ASSIGNMENT'] = on_maintenance
                    calendar_1[day]['ASSIGNED STATE'] = {}
                    for _ in on_maintenance:
                        calendar_1[day]['ASSIGNED STATE'][_] = fleet_state_1[_]
                    childs.append(
                        NodeScheduleDays(
                            calendar_1,
                            day,
                            fleet_state_1,
                            action_value,
                            assignment=on_maintenance,
                            on_c_maintenance=on_c_maintenance_1,
                            on_c_maintenance_tats=on_c_maintenance_tats_1,
                            on_maintenance_merged=on_maintenance_merged))
            if not action_value:
                on_maintenance = []
                fleet_state_0 = self.fleet_operate_one_day(
                    fleet_state_0, day_old, on_maintenance, type_check,
                    on_c_maintenance_0)
                fleet_state_0 = order_fleet_state(fleet_state_0)
                valid = self.check_safety_fleet(fleet_state_0)
                if valid:
                    calendar_0[day] = {}
                    calendar_0[day]['SLOTS'] = slots
                    calendar_0[day]['MAINTENANCE'] = False
                    calendar_0[day]['ASSIGNMENT'] = None
                    childs.append(
                        NodeScheduleDays(
                            calendar_0,
                            day,
                            fleet_state_0,
                            action_value,
                            assignment=on_maintenance,
                            on_c_maintenance=on_c_maintenance_0,
                            on_c_maintenance_tats=on_c_maintenance_tats_0,
                            on_maintenance_merged=on_maintenance_merged))

        return childs

    def expand_c(self, node_schedule, type_check):
        calendar_0 = deepcopy(node_schedule.calendar)
        calendar_1 = deepcopy(node_schedule.calendar)
        fleet_state_0 = deepcopy(node_schedule.fleet_state)
        fleet_state_1 = deepcopy(node_schedule.fleet_state)
        on_c_maintenance_0 = deepcopy(node_schedule.on_c_maintenance)
        on_c_maintenance_1 = deepcopy(node_schedule.on_c_maintenance)
        c_maintenance_counter = deepcopy(node_schedule.c_maintenance_counter)
        on_c_maintenance_tats_0 = deepcopy(node_schedule.on_c_maintenance_tats)
        on_c_maintenance_tats_1 = deepcopy(node_schedule.on_c_maintenance_tats)
        fleet_phasing_out_0 = deepcopy(node_schedule.fleet_phasing_out)
        fleet_phasing_out_1 = deepcopy(node_schedule.fleet_phasing_out)
        phased_out_0 = deepcopy(node_schedule.phased_out)
        phased_out_1 = deepcopy(node_schedule.phased_out)

        day = node_schedule.day
        day_old = day
        childs = []
        day = advance_date(day, days=int(1))
        slots = self.get_slots(day, type_check)
        # if self.calendar_tree['C'].depth() == 668:

        #     import ipdb
        #     ipdb.set_trace()
        # slots += 1

        # if self.calendar_tree['C'].depth() == 677:
        #     import ipdb
        #     ipdb.set_trace()
        # iso_str = '7/1/2021'
        # daterinos = pd.to_datetime(iso_str, format='%m/%d/%Y')
        # if day == daterinos:
        #     import ipdb
        #     ipdb.set_trace()
        # slots += 2

        on_maintenance = list(fleet_state_1.keys())[0]
        ratio = fleet_state_0[on_maintenance]['TOTAL-RATIO']
        if self.calendar_tree['C'].depth() <= 240:
            maintenance_actions = [1, 0] if ratio > 0.65 else [0, 1]
        elif self.calendar_tree['C'].depth() <= 343:
            maintenance_actions = [1, 0] if ratio > 0.65 else [0, 1]
        elif self.calendar_tree['C'].depth() <= 727:
            maintenance_actions = [1, 0] if ratio > 0.65 else [0, 1]
        elif self.calendar_tree['C'].depth() <= 785:
            maintenance_actions = [1, 0] if ratio > 0.75 else [0, 1]
        elif self.calendar_tree['C'].depth() <= 927:
            maintenance_actions = [1, 0] if ratio > 0.8 else [0, 1]
        elif self.calendar_tree['C'].depth() <= 960:
            maintenance_actions = [1, 0] if ratio > 0.8 else [0, 1]
        else:
            maintenance_actions = [1, 0] if ratio > 0.84 else [0, 1]

        fleet_keys = list(fleet_state_0.keys())
        for _ in fleet_keys:
            last_code = self.code_generator['C'](fleet_state_0[_]['C-SN'])
            # last_code = fleet_state_0[_]['C-SN']
            if self.tats[_][last_code] == -1:
                # import ipdb
                # ipdb.set_trace()
                fleet_phasing_out_0[_] = deepcopy(fleet_state_0[_])
                fleet_phasing_out_1[_] = deepcopy(fleet_state_1[_])
                fleet_state_0.pop(_, None)
                fleet_state_1.pop(_, None)
                # import ipdb
                # ipdb.set_trace()

        # if len(on_c_maintenance_0) > 0 and self.calendar_tree['C'].depth() == 21:
        #     import ipdb
        #     ipdb.set_trace()
        on_c_maintenance_all = deepcopy(on_c_maintenance_0)
        for _ in on_c_maintenance_all:
            print("{}-{}".format(_, on_c_maintenance_tats_0[_]))
            if on_c_maintenance_tats_0[_] == 0:
                on_c_maintenance_0.remove(_)
                on_c_maintenance_tats_0.pop(_, None)
                on_c_maintenance_1.remove(_)
                on_c_maintenance_tats_1.pop(_, None)
            else:
                on_c_maintenance_tats_0[_] -= 1
                on_c_maintenance_tats_1[_] -= 1

        # if len(on_c_maintenance_0) > 0 and self.calendar_tree['C'].depth() == 21:
        #     import ipdb
        #     ipdb.set_trace()

        if c_maintenance_counter > 0:
            c_maintenance_counter -= 1

        for action_value in maintenance_actions:
            # if type_check
            if action_value and self.calendar.calendar[day]['allowed'][
                    'public holidays'] and self.calendar.calendar[day][
                        'allowed']['c-type'] and self.calendar.calendar[day][
                            'allowed']['c_peak']:

                on_maintenance = list(fleet_state_1.keys())[0]
                le_d_check = False
                for key in fleet_state_1.keys():
                    d_ratio = fleet_state_1[key]['DY-D-RATIO']
                    if d_ratio >= 1:
                        # import ipdb
                        # ipdb.set_trace()
                        print("OHOH")
                        on_maintenance = key
                        le_d_check = True

                new_code = self.code_generator['C'](
                    fleet_state_1[on_maintenance]['C-SN'])

                valid_c, on_c_maintenance_1, real_tats = self.c_allowed(
                    day, on_maintenance, on_c_maintenance_1, slots,
                    c_maintenance_counter, new_code, on_c_maintenance_tats_1)
                # if self.calendar_tree['C'].depth() == 677:
                #     import ipdb
                #     ipdb.set_trace()

                if valid_c:
                    # if on_maintenance=='Aircraft-48':
                    #     import ipdb
                    #     ipdb.set_trace()
                    is_D_check = (self.is_d_check(on_maintenance,
                                                  fleet_state_1) or le_d_check)
                    fleet_state_1 = self.fleet_operate_one_day(
                        fleet_state_1,
                        day_old,
                        on_c_maintenance_1,
                        type_check=type_check,
                        type_D_check=is_D_check)
                    fleet_state_1 = order_fleet_state(fleet_state_1)
                    fleet_phasing_out_1 = self.fleet_operate_one_day(
                        fleet_phasing_out_1,
                        day_old, [],
                        type_check=type_check)
                    fleet_phasing_out_1, phased_out_1 = self.phasing_out(
                        fleet_phasing_out_1, phased_out_1, day_old)
                    valid = self.check_safety_fleet(fleet_state_1)
                    if valid:
                        calendar_1[day] = {}
                        calendar_1[day]['SLOTS'] = slots
                        calendar_1[day]['MAINTENANCE'] = True
                        calendar_1[day]['ASSIGNMENT'] = on_maintenance
                        calendar_1[day]['ASSIGNED STATE'] = {}
                        calendar_1[day]['ASSIGNED STATE'][
                            'STATE'] = fleet_state_1[on_maintenance]
                        calendar_1[day]['ASSIGNED STATE']['TAT'] = real_tats[
                            on_maintenance]
                        c_maintenance_counter = 3
                        childs.append(
                            NodeScheduleDays(
                                calendar_1,
                                day,
                                fleet_state_1,
                                action_value,
                                assignment=on_maintenance,
                                on_c_maintenance=on_c_maintenance_1,
                                c_maintenance_counter=c_maintenance_counter,
                                on_c_maintenance_tats=real_tats,
                                fleet_phasing_out=fleet_phasing_out_1,
                                phased_out=phased_out_1))

            if not action_value:
                fleet_state_0 = self.fleet_operate_one_day(
                    fleet_state_0, day_old, on_c_maintenance_0, type_check)
                fleet_state_0 = order_fleet_state(fleet_state_0)
                fleet_phasing_out_0 = self.fleet_operate_one_day(
                    fleet_phasing_out_0, day_old, [], type_check)
                fleet_phasing_out_0, phased_out_0 = self.phasing_out(
                    fleet_phasing_out_0, phased_out_0, day_old)
                valid = self.check_safety_fleet(fleet_state_0)
                if valid:
                    calendar_0[day] = {}
                    calendar_0[day]['SLOTS'] = slots
                    calendar_0[day]['MAINTENANCE'] = False
                    calendar_0[day]['ASSIGNMENT'] = None
                    childs.append(
                        NodeScheduleDays(
                            calendar_0,
                            day,
                            fleet_state_0,
                            action_value,
                            assignment=[],
                            on_c_maintenance=on_c_maintenance_0,
                            c_maintenance_counter=c_maintenance_counter,
                            on_c_maintenance_tats=on_c_maintenance_tats_0,
                            fleet_phasing_out=fleet_phasing_out_0,
                            phased_out=phased_out_0))
        return childs

    def is_d_check(self, on_maintenance, fleet_state):
        d_cycle = fleet_state[on_maintenance]['D-CYCLE']
        d_cycle_max = fleet_state[on_maintenance]['D-CYCLE-MAX']

        total_ratio = fleet_state[on_maintenance]['TOTAL-RATIO']
        d_ratio = fleet_state[on_maintenance]['DY-D-RATIO']

        # if on_maintenance == 'Aircraft-48':
        #     import ipdb
        #     ipdb.set_trace()

        if (d_cycle == d_cycle_max) or (d_ratio >= 0.90):
            # import ipdb
            # ipdb.set_trace()
            return True

        if d_ratio >= 1:
            import ipdb
            ipdb.set_trace()
            print("oh no")

        return False

    def phasing_out(self, fleet_phasing_out, phased_out, day):
        fleet_phasing_out_keys = list(fleet_phasing_out.keys())
        for key in fleet_phasing_out_keys:
            dy_d = fleet_phasing_out[key]['DY-D']
            dy_d_max = fleet_phasing_out[key]['DY-D-MAX']
            total_ratio = fleet_phasing_out[key]['TOTAL-RATIO']
            if total_ratio >= 1 or dy_d >= dy_d_max:
                if key == 'Aircraft-13':
                    import ipdb
                    ipdb.set_trace()

                fleet_phasing_out.pop(key, None)
                phased_out[key] = day
                # self.phased_out[key] = day
                # self.removed_aircrafts[key] = day
        return fleet_phasing_out, phased_out

    def c_allowed(self, day, on_maintenance, on_c_maintenance, slots,
                  c_maintenance_counter, new_code, all_maintenance_tats):
        all_maintenance = on_c_maintenance
        all_maintenance.append(on_maintenance)
        assert len(all_maintenance) != 0
        if c_maintenance_counter > 0:  #major bug of all times
            return False, all_maintenance, all_maintenance_tats
        if len(all_maintenance) > slots:
            return False, all_maintenance, all_maintenance_tats
        tat = self.tats[on_maintenance][new_code]
        # se a next tat for -1, metes só phased out
        date = day
        real_tat = 0
        # self.calendar
        while tat > 0:
            date = advance_date(date, days=int(1))
            if self.calendar.calendar[date]['allowed'][
                    'public holidays'] and self.calendar.calendar[date][
                        'allowed']['no_weekends']:
                tat -= 1
            real_tat += 1
        all_maintenance_tats[on_maintenance] = real_tat

        if self.calendar.calendar[date]['allowed'][
                'c_allowed'] and self.calendar.calendar[date]['allowed'][
                    'c_peak']:
            return True, all_maintenance, all_maintenance_tats
        return False, all_maintenance, all_maintenance_tats

    def solve(self, node_schedule, type_check='A', limit=3000):

        if self.check_solved(node_schedule.calendar):
            return node_schedule

        if limit == 0:
            return "cutoff"
        # this could may be used to
        # next_var = self.csp.select_next_var(node_schedule.assignment)
        # if next_var == None:
        #     return None
        cutoff = False
        for child in self.expand_with_heuristic(node_schedule,
                                                type_check=type_check):
            self.calendar_tree[type_check][node_schedule.identifier].count += 1
            if self.calendar_tree[type_check][
                    node_schedule.identifier].count > 1:
                print("BACKTRACKKKKKKKK")

            # print("Child is {}, parent is {}".format(child, node_schedule))
            try:
                self.calendar_tree[type_check].add_node(child, node_schedule)
            except Exception as e:
                import ipdb
                ipdb.set_trace()
                print(e)
            print("Depth:{}".format(self.calendar_tree[type_check].depth()))
            # if self.calendar_tree[type_check].depth() == 950:
            #     global maintenance_actions
            #     maintenance_actions = [0, 1]

            next_node = self.solve(child,
                                   type_check=type_check,
                                   limit=limit - 1)
            if next_node == "cutoff":
                cutoff = True
            elif next_node is not None:
                return next_node
        return "cutoff" if cutoff else None

    def solve_schedule(self, type_check='A'):
        root_id = self.calendar_tree[type_check].root
        root = self.calendar_tree[type_check].get_node(root_id)
        result = self.solve(root, type_check=type_check)
        final_schedule = self.calendar_to_schedule(result, type_check)
        metrics_dict = self.final_schedule_to_excel(final_schedule, type_check)
        self.final_calendar[type_check] = result.calendar
        save_pickle(self.final_calendar, "{}_checks.pkl".format(type_check))
        if type_check == 'C':
            self.phased_out = result.phased_out
        save_pickle(self.phased_out, "phased_out")
        if type_check == 'A':
            save_pickle(metrics_dict, "metrics_dict".format(type_check))
            # metrics = self.metrics(metrics_dict)
        import ipdb
        ipdb.set_trace()
        # result = self.solve(root, type_check='A')
        # score = self.calendar_score(result, type_check=type_check)
        # self.calendar_tree[type_check].show(nid=result.identifier)
        # A optmized: (13261, 9134.300000000052, 103953.90000000001)
        # A non-optimized: (55577, 254913.6, 365113.99999999936)
        return result

    def calendar_to_schedule(self, node_schedule, type_check='A'):
        calendar = deepcopy(node_schedule.calendar)
        schedule = deepcopy(self.finale_schedule)
        for _ in calendar.keys():
            aircraft = calendar[_]['ASSIGNMENT']
            try:
                if aircraft is not None:
                    if type_check == 'C':
                        schedule[aircraft][_] = {}
                        schedule[aircraft][_]['STATE'] = calendar[_][
                            'ASSIGNED STATE']['STATE']
                        schedule[aircraft][_]['TAT'] = calendar[_][
                            'ASSIGNED STATE']['TAT']
                    elif type_check == 'A':
                        for ac in aircraft:
                            schedule[ac][_] = {}
                            schedule[ac][_]['STATE'] = calendar[_][
                                'ASSIGNED STATE'][ac]

            except:
                import ipdb
                ipdb.set_trace()

        return schedule

    def calendar_score(self, node_schedule, type_check='A'):
        score_waste_DY = 0
        score_waste_FH = 0
        score_waste_FC = 0
        all_transverse_nodes = self.calendar_tree[type_check].rsearch(
            node_schedule.identifier)
        for node_id in all_transverse_nodes:
            node = self.calendar_tree[type_check][node_id]
            for aircraft in node.fleet_state.keys():
                if not node.fleet_state[aircraft]['OPERATING']:
                    score_waste_DY += node_schedule.fleet_state[aircraft][
                        'DY-{}-WASTE'.format(type_check)]
                    score_waste_FH += node_schedule.fleet_state[aircraft][
                        'FH-{}-WASTE'.format(type_check)]
                    score_waste_FC += node_schedule.fleet_state[aircraft][
                        'FC-{}-WASTE'.format(type_check)]
        return score_waste_DY, score_waste_FH, score_waste_FC

    # for A and C and both
    def metrics(self, metrics_dict):
        # avg. DY/FH/FC avg.wasted DY/FH/FC
        # avg. worst calendar/best calendar score
        # backtracked, time,
        import statistics

        # import ipdb
        # ipdb.set_trace()
        FH_mean = statistics.mean(map(float, metrics_dict['FH']))
        FH_stdev = statistics.stdev(map(float, metrics_dict['FH']))
        FH_min = min(metrics_dict['FH'])
        FH_max = max(metrics_dict['FH'])

        def ratio_chunks(l, n):
            for i in range(0, len(l), n):
                yield statistics.mean(map(float, l[i:i + n]))

        FHs = list(ratio_chunks(metrics_dict['FH'], 100))
        FH_ratios = [x / 750 for x in FHs]
        # FH_formated = ['%.2f' % x for x in FH_ratios]
        print("###################################")
        print("METRICS")
        print("###################################")
        print("Number of A checks: {}".format(len(metrics_dict['FH'])))
        print("FH mean: {}\nFH stdev: {}\nFH max: {}\nFH min: {}, idx: {}".
              format(FH_mean, FH_stdev, FH_max, FH_min,
                     metrics_dict['FH'].index(FH_min)))
        # print("FH means every 100 days {}".format(FHs))

        import ipdb
        ipdb.set_trace()

    # TODO need to fix the C_elapsed_time
    def final_schedule_to_excel(self, final_schedule, type_check='C'):
        # import ipdb
        # ipdb.set_trace()
        print("INFO: Saving xlsx files")
        dict1 = OrderedDict()
        # dict1['Fleet'] = []
        dict1['A/C ID'] = []
        dict1['START'] = []
        dict1['END'] = []
        dict1['DY'] = []
        dict1['FH'] = []
        dict1['FC'] = []
        dict1['DY LOST'] = []
        dict1['FH LOST'] = []
        dict1['FC LOST'] = []
        for aircraft in final_schedule.keys():
            for _ in final_schedule[aircraft].keys():
                # dict1['Fleet'].append(aircraft[0:4])
                dict1['A/C ID'].append(aircraft)
                dict1['START'].append(pd.to_datetime(_, format='%m/%d/%Y'))
                if type_check == 'C':
                    tat = final_schedule[aircraft][_]['TAT']
                    end_date = advance_date(_, days=tat)
                    dict1['END'].append(
                        pd.to_datetime(end_date, format='%m/%d/%Y'))
                elif type_check == 'A':
                    dict1['END'].append(pd.to_datetime(_, format='%m/%d/%Y'))

                waste_dy = final_schedule[aircraft][_]['STATE'][
                    'DY-{}-WASTE'.format(type_check)]
                waste_fh = final_schedule[aircraft][_]['STATE'][
                    'FH-{}-WASTE'.format(type_check)]
                waste_fc = final_schedule[aircraft][_]['STATE'][
                    'FC-{}-WASTE'.format(type_check)]
                max_dy = final_schedule[aircraft][_]['STATE'][
                    'DY-{}-MAX'.format(type_check)]
                max_fh = final_schedule[aircraft][_]['STATE'][
                    'FH-{}-MAX'.format(type_check)]
                max_fc = final_schedule[aircraft][_]['STATE'][
                    'FC-{}-MAX'.format(type_check)]
                if waste_dy < 0:
                    waste_dy = 0
                if waste_fh < 0:
                    waste_fh = 0
                if waste_fc < 0:
                    waste_fc = 0
                dy = max_dy - waste_dy
                fh = max_fh - waste_fh
                fc = max_fc - waste_fc

                dict1['DY'].append(dy)
                dict1['FH'].append(fh)
                dict1['FC'].append(fc)
                dict1['DY LOST'].append(waste_dy)
                dict1['FH LOST'].append(waste_fh)
                dict1['FC LOST'].append(waste_fc)

        df = pd.DataFrame(dict1, columns=dict1.keys())

        print(df)
        df.to_excel('{}-checks.xlsx'.format(type_check))
        return dict1