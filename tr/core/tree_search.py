import treelib

from treelib import Tree
from tqdm import tqdm
from collections import OrderedDict, deque

from tr.core.utils import advance_date

maintenance_actions = [1, 0]  #the order of this list reflects an heuristc btw


class TreeDaysPlanner:
    def __init__(self, calendar, fleet):
        self.calendar = calendar
        self.fleet = fleet
        self.fleet_state = self.__build_fleet_state()
        self.fleet_state = self.__order_fleet_state()

        self.calendar_tree = Tree()  #calendar tree with data as fleet_state
        self.calendar_simplified = OrderedDict()  #current optimized calendar
        self.root = NodeScheduleDays(calendar=self.calendar_simplified,
                                     day=self.calendar.start_date,
                                     fleet_state=self.fleet_state,
                                     action_maintenance=0,
                                     assignment=[],
                                     tag="Root",
                                     identifier="root")

        self.calendar_tree.add_node(self.root)

        self.schedule_counter = 0
        self.all_schedules = deque(
            maxlen=100)  #maintain only the top 100 schedules

        self.fleet_state = self.__build_fleet_state()
        self.fleet_state = self.__order_fleet_state()

    def __build_fleet_state(self):
        fleet_state = OrderedDict()
        for key in self.fleet.aircraft_info.keys():
            fleet_state[key] = {}
            fleet_state[key]['DY-A'] = self.fleet.aircraft_info[key][
                'A_INITIAL']['DY-A']
            fleet_state[key]['FH-A'] = self.fleet.aircraft_info[key][
                'A_INITIAL']['FH-A']
            fleet_state[key]['FC-A'] = self.fleet.aircraft_info[key][
                'A_INITIAL']['FH-A']
            fleet_state[key]['DY-A-MAX'] = self.fleet.aircraft_info[key][
                'A_INITIAL']['A-CI-DY']
            fleet_state[key]['FH-A-MAX'] = self.fleet.aircraft_info[key][
                'A_INITIAL']['A-CI-FH']
            fleet_state[key]['FC-A-MAX'] = self.fleet.aircraft_info[key][
                'A_INITIAL']['A-CI-FH']
            fleet_state[key]['DFH'] = self.fleet.aircraft_info[key]['DFH']
            fleet_state[key]['DFC'] = self.fleet.aircraft_info[key]['DFC']
            fleet_state[key]['DY-A-RATIO'] = fleet_state[key][
                'DY-A'] / fleet_state[key]['DY-A-MAX']
            fleet_state[key]['FH-A-RATIO'] = fleet_state[key][
                'FH-A'] / fleet_state[key]['FH-A-MAX']
            fleet_state[key]['FC-A-RATIO'] = fleet_state[key][
                'FC-A'] / fleet_state[key]['FC-A-MAX']
            fleet_state[key]['TOTAL-RATIO'] = max([
                fleet_state[key]['DY-A-RATIO'], fleet_state[key]['FH-A-RATIO'],
                fleet_state[key]['FC-A-RATIO']
            ])
            fleet_state[key]['DY-A-WASTE'] = fleet_state[key][
                'DY-A-MAX'] - fleet_state[key]['DY-A']
            fleet_state[key]['FH-A-WASTE'] = fleet_state[key][
                'FH-A-MAX'] - fleet_state[key]['FH-A']
            fleet_state[key]['FC-A-WASTE'] = fleet_state[key][
                'FC-A-MAX'] - fleet_state[key]['FC-A']
            fleet_state[key]['OPERATING'] = True
        return fleet_state

    def __order_fleet_state(self):
        return OrderedDict(
            sorted(self.fleet_state.items(),
                   key=lambda x: x[1]['TOTAL-RATIO'],
                   reverse=True))

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
    def optimize(self):
        for day in self.calendar.calendar.keys():
            slots = self.get_slots(day, check_type='a-type')
            self.optimized_calendar_simplified[day] = {}
            self.optimized_calendar_simplified[day]['SLOTS'] = slots
            self.optimized_calendar_simplified[day][
                'FLEET-STATE'] = self.fleet_state
            schedule, valid = self.run_monte_carlo_greedy()
            if valid:
                self.all_schedules.appendleft(schedule)
            else:
                print("stopped optimizing at day {}".format(day))
                break

            #This piece of code, until line 95 is just a
            #one look ahead
            on_maintenance = []
            fleet_state = self.fleet_operate_one_day(self.fleet_state, day,
                                                     on_maintenance)
            valid = self.check_safety_fleet(fleet_state)
            if not valid:
                on_maintenance = list(fleet_state.keys())[0:slots]
                fleet_state = self.fleet_operate_one_day(
                    self.fleet_state, day, on_maintenance)
                valid = self.check_safety_fleet(fleet_state)
                if valid:
                    self.fleet_state = fleet_state
            day = advance_date(day, days=int(1))
            import ipdb
            ipdb.set_trace()

        print("INFO: Calendar optimized, best schedule found from {}".format(
            self.schedule_counter))

    #exceptions is a list of aircrafts that is in maintenance, thus not operating
    def fleet_operate_one_day(self, fleet_state, date, on_maintenance=[]):
        for aircraft in fleet_state.keys():
            if aircraft in on_maintenance:
                fleet_state[aircraft]['DY-A'] = 0
                fleet_state[aircraft]['FH-A'] = 0
                fleet_state[aircraft]['FC-A'] = 0
                fleet_state[aircraft]['OPERATING'] = False
            else:
                fleet_state[aircraft]['DY-A'] += 1
                month = (date.month_name()[0:3]).upper()
                fleet_state[aircraft]['FH-A'] += fleet_state[aircraft]['DFH'][
                    month]
                fleet_state[aircraft]['FC-A'] += fleet_state[aircraft]['DFC'][
                    month]
                fleet_state[aircraft]['OPERATING'] = True

            fleet_state[aircraft]['DY-A-RATIO'] = fleet_state[aircraft][
                'DY-A'] / fleet_state[aircraft]['DY-A-MAX']
            fleet_state[aircraft]['FH-A-RATIO'] = fleet_state[aircraft][
                'FH-A'] / fleet_state[aircraft]['FH-A-MAX']
            fleet_state[aircraft]['FC-A-RATIO'] = fleet_state[aircraft][
                'FC-A'] / fleet_state[aircraft]['FC-A-MAX']
            fleet_state[aircraft]['TOTAL-RATIO'] = max([
                fleet_state[aircraft]['DY-A-RATIO'],
                fleet_state[aircraft]['FH-A-RATIO'],
                fleet_state[aircraft]['FC-A-RATIO']
            ])
            fleet_state[aircraft]['DY-A-WASTE'] = fleet_state[aircraft][
                'DY-A-MAX'] - fleet_state[aircraft]['DY-A']
            fleet_state[aircraft]['FH-A-WASTE'] = fleet_state[aircraft][
                'FH-A-MAX'] - fleet_state[aircraft]['FH-A']
            fleet_state[aircraft]['FC-A-WASTE'] = fleet_state[aircraft][
                'FC-A-MAX'] - fleet_state[aircraft]['FC-A']
        return fleet_state

    def check_safety_fleet(self, fleet_state):
        for key in fleet_state.keys():
            if fleet_state[key]['TOTAL-RATIO'] >= 100:
                return False
        return True

    def check_solved(self, current_calendar):
        a = len(current_calendar)
        b = len(self.calendar.calendar)
        if a >= b:
            return True
        return False

    #put always in maintenance depending on the number of slots
    def run_monte_carlo_greedy(self):
        fleet_state = self.fleet_state
        valid = self.check_safety_fleet(fleet_state)
        optimized_calendar_simplified = self.optimized_calendar_simplified
        day = list(optimized_calendar_simplified.keys())[-1]
        slots = self.get_slots(day)
        on_maintenance = list(fleet_state.keys())[0:slots]

        import ipdb
        ipdb.set_trace()
        while valid and day <= self.calendar.end_date:
            fleet_state = self.fleet_operate_one_day(fleet_state, day,
                                                     on_maintenance)
            fleet_state = self.__order_fleet_state(fleet_state)

            valid = self.check_safety_fleet(fleet_state)
            day = advance_date(day, days=int(1))

            slots = self.get_slots(day)
            on_maintenance = list(fleet_state.keys())[0:slots]

            optimized_calendar_simplified[day] = {}
            optimized_calendar_simplified[day]['SLOTS'] = slots
            optimized_calendar_simplified[day]['FLEET-STATE'] = fleet_state

        return schedule, valid

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
    def expand_with_heuristic(self, node_schedule):
        calendar = node_schedule.calendar
        fleet_state = node_schedule.fleet_state
        day = node_schedule.day
        day_old = day
        childs = []
        day = advance_date(day, days=int(1))
        slots = self.get_slots(day)
        calendar[day] = {}
        for action_value in maintenance_actions:
            if not action_value:
                on_maintenance = []
                fleet_state = self.fleet_operate_one_day(
                    fleet_state, day_old, on_maintenance)
                valid = self.check_safety_fleet(fleet_state)
                if valid:
                    calendar[day]['SLOTS'] = slots
                    calendar[day]['MAINTENANCE'] = False
                    calendar[day]['ASSIGNMENT'] = on_maintenance
                    childs.append(
                        NodeScheduleDays(calendar,
                                         day,
                                         fleet_state,
                                         action_value,
                                         assignment=on_maintenance))
                    # childs.append(child)
            if action_value and self.calendar.calendar[day]['allowed'][
                    'public holidays'] and self.calendar.calendar[day][
                        'allowed']['a-type']:
                on_maintenance = list(fleet_state.keys())[0:slots]
                import ipdb
                ipdb.set_trace()
                fleet_state = self.fleet_operate_one_day(
                    fleet_state, day_old, on_maintenance)
                valid = self.check_safety_fleet(fleet_state)
                if valid:
                    calendar[day]['SLOTS'] = slots
                    calendar[day]['MAINTENANCE'] = True
                    calendar[day]['ASSIGNMENT'] = on_maintenance
                    childs.append(
                        NodeScheduleDays(calendar,
                                         day,
                                         fleet_state,
                                         action_value,
                                         assignment=on_maintenance))

        return childs
        # return [
        #     self.child_node(csp, assignment, action_var, action_value)
        #     for action_value in assignment.vars_domain[action_var]
        # ]

        # def expand_with_heuristic(self, csp, node_schedule, action_var):
        #     childs = []
        #     for action_value in csp.select_next_values(node_schedule.assignment,
        #                                                action_var):
        #         child = self.child_node(csp, node_schedule, action_var,
        #                                 action_value)
        #         if child != None and len(childs) == 0:
        #             childs.append(child)
        #         elif child != None and child.tag != childs[-1].tag:
        #             childs.append(child)

        # aux = [child.tag for child in childs]
        # import ipdb
        # ipdb.set_trace()
        # return childs
    def solve(self, node_schedule, limit=2):
        if self.check_solved(node_schedule.calendar):
            return node_schedule

        if limit == 0:
            return "cutoff"

        # next_var = self.csp.select_next_var(node_schedule.assignment)
        # if next_var == None:
        #     return None

        cutoff = False
        for child in self.expand_with_heuristic(node_schedule):
            self.calendar_tree[node_schedule.identifier].count += 1
            if self.calendar_tree[node_schedule.identifier].count > 1:
                print("BACKTRACKKKKKKKK")

            print("Child is {}, parent is {}".format(child, node_schedule))
            try:
                self.calendar_tree.add_node(child, node_schedule)
            except Exception as e:
                print(e)
                import ipdb
                ipdb.set_trace()
            print("Depth:{}".format(self.calendar_tree.depth()))

            next_node = self.solve(child, limit - 1)
            if next_node == "cutoff":
                cutoff = True
            elif next_node != None:
                return next_node
        return "cutoff" if cutoff else None

    # def child_node(self, csp, node_schedule, action_var, action_value):
    #     next_assignment = csp.do_next_assignment(node_schedule.assignment,
    #                                              action_var, action_value)
    #     if next_assignment != None:
    #         return NodeSchedule(next_assignment,
    #                             action_var=action_var,
    #                             action_value=action_value,
    #                             pai=node_schedule.identifier)
    #     return None

    def solve_schedule(self):
        # csp_problem = CSPSchedule(assignment_start.vars)
        # backtrack = BacktrackTreelib(csp_problem, assignment_start)
        # # import ipdb
        # # ipdb.set_trace()
        # root = backtrack.tree.get_node(backtrack.tree.root)
        # result = backtrack.solve(root)
        # ipdb.set_trace()
        result = self.solve(self.root)
        import ipdb
        ipdb.set_trace()
        return result


class BacktrackPlanDays:
    def __init__(self, csp, fleet_state, *args, **kwargs):
        self.csp = csp
        self.start_assign = start_assign
        self.tree = Tree()
        root = NodeSchedule(tag="Root", identifier="root")
        self.tree.add_node(root)

    def solve(self, node_schedule, limit=100):
        if self.csp.satisfied_assignment(node_schedule.assignment):
            return node_schedule

        if limit == 0:
            return "cutoff"

        next_var = self.csp.select_next_var(node_schedule.assignment)
        if next_var == None:
            return None

        cutoff = False
        # here when we expand the childs, we need to fix domain
        for child in node_schedule.expand_with_heuristic(
                self.csp, node_schedule, next_var):
            self.tree[node_schedule.identifier].count += 1
            if self.tree[node_schedule.identifier].count > 1:
                import ipdb
                ipdb.set_trace()
                # check_feasibility(self.start_assign)
                assert False
                print("BACKTRACKKKKKKKK")

            self.tree.add_node(child, node_schedule)
            # print("Depth:{}".format(self.tree.depth()))3

            next_node = self.solve(child, limit - 1)
            if next_node == "cutoff":
                cutoff = True
            elif next_node != None:
                return next_node
        return "cutoff" if cutoff else None


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