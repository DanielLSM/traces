import treelib

from treelib import Tree
from tqdm import tqdm
from collections import OrderedDict, deque
from copy import deepcopy
from tr.core.utils import advance_date

maintenance_actions = [0, 1]  #the order of this list reflects an heuristc btw
type_checks = ['A', 'C']  #type of checks


class TreeDaysPlanner:
    def __init__(self, calendar, fleet):
        self.calendar = calendar
        self.fleet = fleet

        # self.fleet_state = self.__build_fleet_state(type_check='A')
        # self.fleet_state = self.order_fleet_state(self.fleet_state)

        self.calendar_tree = {
            'A': Tree(),
            'C': Tree()
        }  #calendar tree with data as fleet_state

        for type_check in type_checks:
            fleet_state = self.__build_fleet_state(type_check=type_check)
            fleet_state = self.order_fleet_state(fleet_state)

            root = NodeScheduleDays(calendar=OrderedDict(),
                                    day=self.calendar.start_date,
                                    fleet_state=fleet_state,
                                    action_maintenance=0,
                                    assignment=[],
                                    tag="Root",
                                    identifier="root")

            self.calendar_tree[type_check].add_node(root)

        self.schedule_counter = 0
        self.all_schedules = deque(maxlen=100)  #maintain only the top 10

    def __build_fleet_state(self, type_check='A'):
        fleet_state = OrderedDict()
        for key in self.fleet.aircraft_info.keys():
            fleet_state[key] = {}
            fleet_state[key]['DY-{}'.format(
                type_check)] = self.fleet.aircraft_info[key][
                    '{}_INITIAL'.format(type_check)]['DY-{}'.format(
                        type_check)]
            fleet_state[key]['FH-{}'.format(
                type_check)] = self.fleet.aircraft_info[key][
                    '{}_INITIAL'.format(type_check)]['FH-{}'.format(
                        type_check)]
            fleet_state[key]['FC-{}'.format(
                type_check)] = self.fleet.aircraft_info[key][
                    '{}_INITIAL'.format(type_check)]['FH-{}'.format(
                        type_check)]
            fleet_state[key]['DY-{}-MAX'.format(
                type_check)] = self.fleet.aircraft_info[key][
                    '{}_INITIAL'.format(type_check)]['{}-CI-DY'.format(
                        type_check)]
            fleet_state[key]['FH-{}-MAX'.format(
                type_check)] = self.fleet.aircraft_info[key][
                    '{}_INITIAL'.format(type_check)]['{}-CI-FH'.format(
                        type_check)]
            fleet_state[key]['FC-{}-MAX'.format(
                type_check)] = self.fleet.aircraft_info[key][
                    '{}_INITIAL'.format(type_check)]['{}-CI-FH'.format(
                        type_check)]
            fleet_state[key]['DFH'] = self.fleet.aircraft_info[key]['DFH']
            fleet_state[key]['DFC'] = self.fleet.aircraft_info[key]['DFC']
            fleet_state[key]['DY-{}-RATIO'.format(
                type_check
            )] = fleet_state[key]['DY-{}'.format(
                type_check)] / fleet_state[key]['DY-{}-MAX'.format(type_check)]
            fleet_state[key]['FH-{}-RATIO'.format(
                type_check
            )] = fleet_state[key]['FH-{}'.format(
                type_check)] / fleet_state[key]['FH-{}-MAX'.format(type_check)]
            fleet_state[key]['FC-{}-RATIO'.format(
                type_check
            )] = fleet_state[key]['FC-{}'.format(
                type_check)] / fleet_state[key]['FC-{}-MAX'.format(type_check)]
            fleet_state[key]['TOTAL-RATIO'] = max([
                fleet_state[key]['DY-{}-RATIO'.format(type_check)],
                fleet_state[key]['FH-{}-RATIO'.format(type_check)],
                fleet_state[key]['FC-{}-RATIO'.format(type_check)]
            ])
            fleet_state[key]['DY-{}-WASTE'.format(
                type_check)] = fleet_state[key]['DY-{}-MAX'.format(
                    type_check)] - fleet_state[key]['DY-{}'.format(type_check)]
            fleet_state[key]['FH-{}-WASTE'.format(
                type_check)] = fleet_state[key]['FH-{}-MAX'.format(
                    type_check)] - fleet_state[key]['FH-{}'.format(type_check)]
            fleet_state[key]['FC-{}-WASTE'.format(
                type_check)] = fleet_state[key]['FC-{}-MAX'.format(
                    type_check)] - fleet_state[key]['FC-{}'.format(type_check)]
            fleet_state[key]['OPERATING'] = True
        return fleet_state

    def order_fleet_state(self, fleet_state):
        return OrderedDict(
            sorted(fleet_state.items(),
                   key=lambda x: x[1]['TOTAL-RATIO'],
                   reverse=True))

    #exceptions is a list of aircrafts that is in maintenance, thus not operating
    def fleet_operate_one_day(self,
                              fleet_state,
                              date,
                              on_maintenance=[],
                              type_check='A'):
        for aircraft in fleet_state.keys():
            if aircraft in on_maintenance:
                fleet_state[aircraft]['DY-{}-WASTE'.format(
                    type_check)] = fleet_state[aircraft]['DY-{}-MAX'.format(
                        type_check)] - fleet_state[aircraft]['DY-{}'.format(
                            type_check)]
                fleet_state[aircraft]['FH-{}-WASTE'.format(
                    type_check)] = fleet_state[aircraft]['FH-{}-MAX'.format(
                        type_check)] - fleet_state[aircraft]['FH-{}'.format(
                            type_check)]
                fleet_state[aircraft]['FC-{}-WASTE'.format(
                    type_check)] = fleet_state[aircraft]['FC-{}-MAX'.format(
                        type_check)] - fleet_state[aircraft]['FC-{}'.format(
                            type_check)]
                fleet_state[aircraft]['DY-{}'.format(type_check)] = 0
                fleet_state[aircraft]['FH-{}'.format(type_check)] = 0
                fleet_state[aircraft]['FC-{}'.format(type_check)] = 0
                fleet_state[aircraft]['OPERATING'] = False
            else:
                fleet_state[aircraft]['DY-{}'.format(type_check)] += 1
                month = (date.month_name()[0:3]).upper()
                fleet_state[aircraft]['FH-{}'.format(
                    type_check)] += fleet_state[aircraft]['DFH'][month]
                fleet_state[aircraft]['FC-{}'.format(
                    type_check)] += fleet_state[aircraft]['DFC'][month]
                fleet_state[aircraft]['OPERATING'] = True

            fleet_state[aircraft]['DY-{}-RATIO'.format(
                type_check)] = fleet_state[aircraft]['DY-{}'.format(
                    type_check)] / fleet_state[aircraft]['DY-{}-MAX'.format(
                        type_check)]
            fleet_state[aircraft]['FH-{}-RATIO'.format(
                type_check)] = fleet_state[aircraft]['FH-{}'.format(
                    type_check)] / fleet_state[aircraft]['FH-{}-MAX'.format(
                        type_check)]
            fleet_state[aircraft]['FC-{}-RATIO'.format(
                type_check)] = fleet_state[aircraft]['FC-{}'.format(
                    type_check)] / fleet_state[aircraft]['FC-{}-MAX'.format(
                        type_check)]
            fleet_state[aircraft]['TOTAL-RATIO'] = max([
                fleet_state[aircraft]['DY-{}-RATIO'.format(type_check)],
                fleet_state[aircraft]['FH-{}-RATIO'.format(type_check)],
                fleet_state[aircraft]['FC-{}-RATIO'.format(type_check)]
            ])
        return fleet_state

    def check_safety_fleet(self, fleet_state):
        for key in fleet_state.keys():
            if fleet_state[key]['TOTAL-RATIO'] >= 1:
                return False
        return True

    def check_solved(self, current_calendar):
        a = len(current_calendar)
        b = len(self.calendar.calendar)
        b = len(range(1000))
        if a >= b:
            return True
        return False

    def get_slots(self, date, check_type='a-type'):

        check_types = ['a-type', 'c-type']
        slots = [
            self.calendar.calendar[date]['resources']['slots'][check]
            for check in check_types
        ]
        max_slots = max(slots)

        slots = max_slots
        # check_types = ['a-type', 'c-type']
        # slots = [
        #     self.calendar.calendar[date]['resources']['slots'][check]
        #     for check in check_types
        # ]

        # slots = self.calendar.calendar[date]['resources']['slots'][check_type]

        return slots

    #there is no variables, just one bolean variable, do maintenance or not
    def expand_with_heuristic(self, node_schedule, type_check='A'):
        calendar_0 = deepcopy(node_schedule.calendar)
        calendar_1 = deepcopy(node_schedule.calendar)
        fleet_state_0 = deepcopy(node_schedule.fleet_state)
        fleet_state_1 = deepcopy(node_schedule.fleet_state)

        day = node_schedule.day
        day_old = day
        childs = []
        day = advance_date(day, days=int(1))
        slots = self.get_slots(day) + 2
        calendar_0[day] = {}
        calendar_1[day] = {}

        for action_value in maintenance_actions:
            if action_value and self.calendar.calendar[day]['allowed'][
                    'public holidays'] and self.calendar.calendar[day][
                        'allowed']['a-type']:
                on_maintenance = list(fleet_state_1.keys())[0:slots]
                fleet_state_1 = self.fleet_operate_one_day(
                    fleet_state_1, day_old, on_maintenance, type_check)
                fleet_state_1 = self.order_fleet_state(fleet_state_1)

                valid = self.check_safety_fleet(fleet_state_1)
                if valid:
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
                fleet_state_0 = self.order_fleet_state(fleet_state_0)
                valid = self.check_safety_fleet(fleet_state_0)
                if valid:
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

    def solve(self, node_schedule, type_check='A', limit=1000):
        if self.check_solved(node_schedule.calendar):
            return node_schedule

        if limit == 0:
            return "cutoff"

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
            elif next_node != None:
                return next_node
        return "cutoff" if cutoff else None

    def solve_schedule(self, type_check='A'):
        root_id = self.calendar_tree[type_check].root
        root = self.calendar_tree[type_check].get_node(root_id)
        result = self.solve(root, type_check=type_check)
        a1 = self.calendar_tree[type_check].all_nodes()
        for _ in a1[1].fleet_state.keys():
            print(a1[1].fleet_state[_]['TOTAL-RATIO'])

        score = self.calendar_score(result, type_check=type_check)
        self.calendar_tree[type_check].show(nid=result.identifier)
        # A optmized: (13261, 9134.300000000052, 103953.90000000001)
        # A non-optimized: (55577, 254913.6, 365113.99999999936)

        import ipdb
        ipdb.set_trace()

        return result

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


#TODO you should be able to start from an assignment or a tree


class NodeScheduleDays(treelib.Node):
    def __init__(self,
                 calendar,
                 day,
                 fleet_state,
                 action_maintenance,
                 assignment=[],
                 tag=None,
                 identifier=None,
                 *args,
                 **kwargs):
        day_str = day.strftime("%m/%d/%Y")
        # import ipdb
        # ipdb.set_trace()
        if tag == None:
            tag = '{}_{}'.format(day_str, action_maintenance)
        # if identifier == None:
        #     identifier = day_str
        #     for _ in assignment:
        #         identifier = identifier + '/{}'.format(_)

        # print("Creating Node {}".format(tag))
        # super().__init__(tag=tag, identifier=identifier, *args, **kwargs)
        super().__init__(tag=tag, *args, **kwargs)
        self.calendar = calendar
        self.day = day
        self.fleet_state = fleet_state
        self.assignment = assignment  #state of the world
        self.action_maintenance = action_maintenance
        self.count = 0

    #put always in maintenance depending on the number of slots
    # def run_monte_carlo_greedy(self):
    #     fleet_state = self.fleet_state
    #     valid = self.check_safety_fleet(fleet_state)
    #     optimized_calendar_simplified = self.optimized_calendar_simplified
    #     day = list(optimized_calendar_simplified.keys())[-1]
    #     slots = self.get_slots(day) + 5
    #     on_maintenance = list(fleet_state.keys())[0:slots]

    #     import ipdb
    #     ipdb.set_trace()
    #     while valid and day <= self.calendar.end_date:
    #         fleet_state = self.fleet_operate_one_day(fleet_state, day,
    #                                                  on_maintenance)
    #         fleet_state = self.order_fleet_state(fleet_state)

    #         valid = self.check_safety_fleet(fleet_state)
    #         day = advance_date(day, days=int(1))

    #         slots = self.get_slots(day)
    #         on_maintenance = list(fleet_state.keys())[0:slots]

    #         optimized_calendar_simplified[day] = {}
    #         optimized_calendar_simplified[day]['SLOTS'] = slots
    #         optimized_calendar_simplified[day]['FLEET-STATE'] = fleet_state

    #     return schedule, valid

    #here we could implment CSP backtrack... cause a 1 day check is prolly not enough
    #TODO: Need to make backtracking (DFS), yet again...
    #IF NOT MAINTENANCE IS NOT VALID, BUT DOING ALWAYS MIANTENANCE IS, JUST DO MAINTENANCE
    #AND TEST AGAIN, BUT MIGHT BE THAT IT WOULDVE BEEN VALID IF WITH MAINTENANCE BEFORE,
    #SO WE NEED BACKTRACK,
    #ALSO IF YOU HAD TO DO MAINTENANCE AGAIN, DONT COMPUTE GREEDY AGAIN.. IS THIS SAME
    #SCHEDULE, IF, ALTHOUGH, YOU DID A NO MAINTENANCE DAY, YOU CAN GO GREEDY AGAIN,
    #WAIT, IF GREEDY FAILS IT DOESNT MEAN IT HAS TO STOP, IT MEANS THAT PERHAPS SOME NON-MAINTENANCE
    #WERE TOO MUCH

    #YOU CAN ALSO PUT, IF SOMETHING IS ABOVE 95% UTILIZATION, THEN, DO MAINTENANCE
    #YOU CAN ALSO DO MAINTENANCE ON THE LEAST DOMAIN ONES, IF YOU COMPUTE DUE DATES
    # def optimize(self):
    #     for day in self.calendar.calendar.keys():
    #         slots = self.get_slots(day, check_type='a-type')
    #         self.optimized_calendar_simplified[day] = {}
    #         self.optimized_calendar_simplified[day]['SLOTS'] = slots
    #         self.optimized_calendar_simplified[day][
    #             'FLEET-STATE'] = self.fleet_state
    #         schedule, valid = self.run_monte_carlo_greedy()
    #         if valid:
    #             self.all_schedules.appendleft(schedule)
    #         else:
    #             print("stopped optimizing at day {}".format(day))
    #             break

    #         #This piece of code, until line 95 is just a
    #         #one look ahead
    #         on_maintenance = []
    #         fleet_state = self.fleet_operate_one_day(self.fleet_state, day,
    #                                                  on_maintenance)
    #         valid = self.check_safety_fleet(fleet_state)
    #         if not valid:
    #             on_maintenance = list(fleet_state.keys())[0:slots]
    #             fleet_state = self.fleet_operate_one_day(
    #                 self.fleet_state, day, on_maintenance)
    #             valid = self.check_safety_fleet(fleet_state)
    #             if valid:
    #                 self.fleet_state = fleet_state
    #         day = advance_date(day, days=int(1))
    #     print("INFO: Calendar optimized, best schedule found from {}".format(
    #         self.schedule_counter))


# def expand_with_heuristic(self, node_schedule):
#         calendar = node_schedule.calendar
#         fleet_state = node_schedule.fleet_state
#         day = node_schedule.day
#         day_old = day
#         childs = []
#         day = advance_date(day, days=int(1))
#         slots = self.get_slots(day) + 1
#         calendar[day] = {}
#         for action_value in maintenance_actions:
#             if not action_value:
#                 on_maintenance = []
#                 fleet_state_0 = self.fleet_operate_one_day(
#                     fleet_state, day_old, on_maintenance)
#                 fleet_state_0 = self.order_fleet_state(fleet_state_0)
#                 valid = self.check_safety_fleet(fleet_state_0)
#                 if valid:
#                     calendar[day]['SLOTS'] = slots
#                     calendar[day]['MAINTENANCE'] = False
#                     calendar[day]['ASSIGNMENT'] = on_maintenance
#                     childs.append(
#                         NodeScheduleDays(calendar,
#                                          day,
#                                          fleet_state_0,
#                                          action_value,
#                                          assignment=on_maintenance))
#                     # childs.append(child)
#             if action_value and self.calendar.calendar[day]['allowed'][
#                     'public holidays'] and self.calendar.calendar[day][
#                         'allowed']['a-type']:
#                 on_maintenance = list(fleet_state.keys())[0:slots]
#                 fleet_state_1 = self.fleet_operate_one_day(
#                     fleet_state, day_old, on_maintenance)
#                 fleet_state_1 = self.order_fleet_state(fleet_state_1)
#                 valid = self.check_safety_fleet(fleet_state_1)
#                 if valid:
#                     calendar[day]['SLOTS'] = slots
#                     calendar[day]['MAINTENANCE'] = True
#                     calendar[day]['ASSIGNMENT'] = on_maintenance
#                     childs.append(
#                         NodeScheduleDays(calendar,
#                                          day,
#                                          fleet_state_1,
#                                          action_value,
#                                          assignment=on_maintenance))
#         return childs