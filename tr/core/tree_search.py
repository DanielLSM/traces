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

from tr.core.utils import advance_date, save_pickle, load_pickle

maintenance_actions = [1, 0]  # the order of this list reflects an heuristc btw
type_checks = ['A', 'C']  # type of checks


class TreeDaysPlanner:
    def __init__(self, calendar, fleet):
        self.calendar = calendar
        self.fleet = fleet
        self.calendar_tree = {'A': Tree(), 'C': Tree()}
        # self.final_schedule = {'A': {}, 'C': {}}
        try:
            self.final_calendar = load_pickle("c_checks.pkl")
            # self.final_calendar = {'A': {}, 'C': {}}
        except:
            self.final_calendar = {'A': {}, 'C': {}}

        self.removed_aircrafts = []
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
                              type_check='A'):
        kwargs = {
            'fleet_state': fleet_state,
            'date': date,
            'on_maintenance': on_maintenance,
            'type_check': type_check,
            'utilization_ratio': self.utilization_ratio,
            'code_generator': self.code_generator
        }
        # import ipdb
        # ipdb.set_trace()
        if type_check == 'A':
            fleet_state = fleet_operate_A(**kwargs)
        elif type_check == 'C':
            fleet_state = fleet_operate_C(**kwargs)
        return fleet_state

    def check_safety_fleet(self, fleet_state):
        for key in fleet_state.keys():
            if fleet_state[key]['TOTAL-RATIO'] >= 1:
                return False
        return True

    def check_solved(self, current_calendar):
        iso_str = '1/1/2022'
        daterinos = pd.to_datetime(iso_str, format='%m/%d/%Y')
        if len(current_calendar) > 0:
            if list(current_calendar.keys())[-1] == daterinos:
                return True
            else:
                return False
        return False
        # a = len(current_calendar)

        # b = len(self.calendar.calendar) - 1
        # # b = len(range(1000))
        # if a >= b:
        #     return True
        # return False

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
        day = node_schedule.day
        day_old = day
        childs = []
        day = advance_date(day, days=int(1))
        slots = self.get_slots(day, type_check)
        import ipdb
        ipdb.set_trace()
        on_c_calendar = self.final_calendar['C'][day]['ASSIGNMENT']
        on_c_calendar = self.final_calendar['C'][day]['ASSIGNMENT']

        for action_value in maintenance_actions:
            # if type_check
            if action_value and self.calendar.calendar[day]['allowed'][
                    'public holidays'] and self.calendar.calendar[day][
                        'allowed']['a-type']:
                on_maintenance = list(fleet_state_1.keys())[0:slots]
                fleet_state_1 = self.fleet_operate_one_day(
                    fleet_state_1, day_old, on_maintenance, type_check)
                fleet_state_1 = order_fleet_state(fleet_state_1)

                valid = self.check_safety_fleet(fleet_state_1)
                if valid:
                    calendar_1[day] = {}
                    calendar_1[day]['SLOTS'] = slots
                    calendar_1[day]['MAINTENANCE'] = True
                    calendar_1[day]['ASSIGNMENT'] = on_maintenance
                    childs.append(
                        NodeScheduleDays(calendar_1,
                                         day,
                                         fleet_state_1,
                                         action_value,
                                         assignment=on_maintenance))
            if not action_value:
                on_maintenance = []
                fleet_state_0 = self.fleet_operate_one_day(
                    fleet_state_0, day_old, on_maintenance, type_check)
                fleet_state_0 = order_fleet_state(fleet_state_0)
                valid = self.check_safety_fleet(fleet_state_0)
                if valid:
                    calendar_0[day] = {}
                    calendar_0[day]['SLOTS'] = slots
                    calendar_0[day]['MAINTENANCE'] = False
                    calendar_0[day]['ASSIGNMENT'] = on_maintenance
                    childs.append(
                        NodeScheduleDays(calendar_0,
                                         day,
                                         fleet_state_0,
                                         action_value,
                                         assignment=on_maintenance))
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
        day = node_schedule.day
        day_old = day
        childs = []
        day = advance_date(day, days=int(1))
        slots = self.get_slots(day, type_check)
        iso_str = '7/1/2021'
        daterinos = pd.to_datetime(iso_str, format='%m/%d/%Y')
        if day == daterinos:
            import ipdb
            ipdb.set_trace()
            slots += 2

        fleet_keys = list(fleet_state_0.keys())
        for _ in fleet_keys:
            last_code = self.code_generator['C'](fleet_state_0[_]['C-SN'])
            # last_code = fleet_state_0[_]['C-SN']
            if self.tats[_][last_code] == -1:
                fleet_state_0.pop(_, None)
                fleet_state_1.pop(_, None)
                self.removed_aircrafts.append(_)

        for _ in on_c_maintenance_0:
            print("{}-{}".format(_, on_c_maintenance_tats_0[_]))
            if on_c_maintenance_tats_0[_] < 0:
                import ipdb
                ipdb.set_trace()
            on_c_maintenance_tats_0[_] -= 1
            on_c_maintenance_tats_1[_] -= 1
            if on_c_maintenance_tats_0[_] == 0:
                # import ipdb
                # ipdb.set_trace()
                on_c_maintenance_0.remove(_)
                on_c_maintenance_tats_0.pop(_, None)
                on_c_maintenance_1.remove(_)
                on_c_maintenance_tats_1.pop(_, None)
                # if self.tat[_][last_code] == -1: easiest bug to solve in my life

        if c_maintenance_counter > 0:
            c_maintenance_counter -= 1
            # c_maintenance_counter -= 0 stupidest bug ever...

        for action_value in maintenance_actions:
            # if type_check
            if action_value and self.calendar.calendar[day]['allowed'][
                    'public holidays'] and self.calendar.calendar[day][
                        'allowed']['c-type'] and self.calendar.calendar[day][
                            'allowed']['c_peak']:
                on_maintenance = list(fleet_state_1.keys())[0]
                new_code = self.code_generator['C'](
                    fleet_state_1[on_maintenance]['C-SN'])

                valid_c, on_c_maintenance_1, real_tats = self.c_allowed(
                    day, on_maintenance, on_c_maintenance_1, slots,
                    c_maintenance_counter, new_code, on_c_maintenance_tats_1)
                if valid_c:
                    fleet_state_1 = self.fleet_operate_one_day(
                        fleet_state_1, day_old, on_c_maintenance_1, type_check)
                    fleet_state_1 = order_fleet_state(fleet_state_1)

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
                                on_c_maintenance_tats=real_tats))

            if not action_value:
                fleet_state_0 = self.fleet_operate_one_day(
                    fleet_state_0, day_old, on_c_maintenance_0, type_check)
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
                            assignment=[],
                            on_c_maintenance=on_c_maintenance_0,
                            c_maintenance_counter=c_maintenance_counter,
                            on_c_maintenance_tats=on_c_maintenance_tats_0))

        return childs

    def c_allowed(self, day, on_maintenance, on_c_maintenance, slots,
                  c_maintenance_counter, new_code, all_maintenance_tats):
        all_maintenance = on_c_maintenance
        all_maintenance.append(on_maintenance)
        assert len(all_maintenance) != 0
        if c_maintenance_counter > 0:
            return False, all_maintenance, all_maintenance_tats
        if len(all_maintenance) >= slots:
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
                # import ipdb
                # ipdb.set_trace()
                # for _ in node_schedule.calendar.keys():
                #     if len(node_schedule.calendar[_]['ASSIGNMENT']) == 3:
                #         print(hey)
                # import ipdb
                # ipdb.set_trace()
                print("BACKTRACKKKKKKKK")

            print("Child is {}, parent is {}".format(child, node_schedule))
            try:
                self.calendar_tree[type_check].add_node(child, node_schedule)
            except Exception as e:
                import ipdb
                ipdb.set_trace()
                print(e)
            print("Depth:{}".format(self.calendar_tree[type_check].depth()))

            next_node = self.solve(child,
                                   type_check=type_check,
                                   limit=limit - 1)
            if next_node == "cutoff":
                cutoff = True
            elif next_node is not None:
                return next_node
        return "cutoff" if cutoff else None

    def solve_schedule(self, type_check='C'):
        root_id = self.calendar_tree[type_check].root
        root = self.calendar_tree[type_check].get_node(root_id)
        result = self.solve(root, type_check=type_check)
        import ipdb
        ipdb.set_trace()

        final_schedule = self.calendar_to_schedule(result)
        self.final_schedule_to_excel(final_schedule, type_check)
        self.final_calendar[type_check] = result.calendar
        save_pickle(self.final_calendar, "{}_checks.pkl".format(type_check))
        import ipdb
        ipdb.set_trace()
        # result = self.solve(root, type_check='A')
        # score = self.calendar_score(result, type_check=type_check)
        # self.calendar_tree[type_check].show(nid=result.identifier)
        # A optmized: (13261, 9134.300000000052, 103953.90000000001)
        # A non-optimized: (55577, 254913.6, 365113.99999999936)
        return result

    def calendar_to_schedule(self, node_schedule, type_check='C'):
        calendar = deepcopy(node_schedule.calendar)
        schedule = deepcopy(self.finale_schedule)
        # import ipdb
        # ipdb.set_trace()
        for _ in calendar.keys():
            aircraft = calendar[_]['ASSIGNMENT']
            if aircraft is not None:
                schedule[aircraft][_] = {}
                schedule[aircraft][_]['STATE'] = calendar[_]['ASSIGNED STATE'][
                    'STATE']
                schedule[aircraft][_]['TAT'] = calendar[_]['ASSIGNED STATE'][
                    'TAT']
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
    def metrics(self):
        # avg. DY/FH/FC avg.wasted DY/FH/FC
        # avg. worst calendar/best calendar score
        # backtracked, time,
        pass

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
                tat = final_schedule[aircraft][_]['TAT']
                end_date = advance_date(_, days=tat)
                dict1['END'].append(pd.to_datetime(end_date,
                                                   format='%m/%d/%Y'))
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
        df.to_excel('checks.xlsx')