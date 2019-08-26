import treelib

from treelib import Tree
from tqdm import tqdm
from collections import OrderedDict, deque

from tr.core.utils import advance_date


class TreeDaysPlanner:
    def __init__(self, calendar, fleet):
        self.calendar = calendar
        self.fleet = fleet

        self.calendar_tree = Tree()  #calendar tree with data as fleet_state
        self.optimized_calendar_simplified = OrderedDict(
        )  #current optimized calendar
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
                fleet_state[key]['DY-A'] = 0
                fleet_state[key]['FH-A'] = 0
                fleet_state[key]['FC-A'] = 0
                fleet_state[key]['OPERATING'] = False
            else:
                fleet_state[key]['DY-A'] += 1
                month = (date.month_name()[0:3]).upper()
                fleet_state[key]['FH-A'] += fleet_state[key]['DFH'][month]
                fleet_state[key]['FC-A'] += fleet_state[key]['DFC'][month]
                fleet_state[key]['OPERATING'] = True

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
        return fleet_state

    def check_safety_fleet(self, fleet_state):
        for key in fleet_state.keys():
            if fleet_state[key]['TOTAL-RATIO'] > 1:
                return False
        return True

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

        # check_types = ['a-type', 'c-type']
        # slots = [
        #     self.calendar.calendar[date]['resources']['slots'][check]
        #     for check in check_types
        # ]
        # max_slots = max(slots)

        check_types = ['a-type', 'c-type']
        # slots = [
        #     self.calendar.calendar[date]['resources']['slots'][check]
        #     for check in check_types
        # ]

        slots = self.calendar.calendar[date]['resources']['slots'][check_type]

        return slots


class BacktrackPlanDays:
    def __init__(self, csp, start_assign, *args, **kwargs):
        self.csp = csp
        self.start_assign = start_assign
        self.tree = Tree()
        root = NodeSchedule(self.start_assign, tag="Root", identifier="root")
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
def solve_csp_schedule(assignment_start):
    csp_problem = CSPSchedule(assignment_start.vars)
    backtrack = BacktrackTreelib(csp_problem, assignment_start)
    # import ipdb
    # ipdb.set_trace()
    root = backtrack.tree.get_node(backtrack.tree.root)
    result = backtrack.solve(root)
    # ipdb.set_trace()
    return result.assignment, backtrack.tree


class NodeScheduleDays(treelib.Node):
    def __init__(self,
                 assignment,
                 day=None,
                 action_value=None,
                 tag=None,
                 identifier=None,
                 pai=None,
                 *args,
                 **kwargs):
        if tag == None:
            tag = day
            # tag = ''
            # for _ in assignment:
            #     tag += '/{}'.format(_)
            # tag = "{}={}".format(action_var, action_value)
        if identifier == None:
            # identifier = "{}={}_from_{}".format(action_var, action_value, pai)
            # identifier = "{}={}_from_{}".format(action_var, action_value, pai)
            identifier = tag
            for _ in assignment:
                identifier += '/{}'.format(_)

        # print("Creating Node {}".format(tag))
        super().__init__(tag=tag, identifier=identifier, *args, **kwargs)
        self.assignment = assignment  #state of the world
        self.action_var = action_var
        self.action_value = action_value
        self.count = 0
