import treelib

from collections import OrderedDict, deque
from treelib import Tree
from tqdm import tqdm


class TreeDaysPlanner:
    def __init__(self, calendar, fleet):
        self.calendar = calendar
        self.calendar_tree = Tree()  #calendar tree with data as fleet_state
        self.fleet = fleet
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

    def enumerate_all_schedules(self):

        #current optimized calendar being built
        optimized_calendar_simplified = OrderedDict()
        current_schedule_counter = 0

        #lets use a deque here, we want to maintain only the top 100 schedules
        all_schedules = deque(maxlen=100)

        import ipdb
        ipdb.set_trace()

        for day in self.calendar.keys():
            pass


class BacktrackTreelib:
    def __init__(self, csp, start_assign, *args, **kwargs):
        assert isinstance(csp, CSPSchedule), "problem is not CSP"
        assert isinstance(start_assign, Assignment), "assignment is not valid"
        self.csp = csp
        self.start_assign = start_assign
        self.tree = Tree()
        root = NodeSchedule(self.start_assign, tag="Root", identifier="root")
        self.tree.add_node(root)


class NodeSchedule(treelib.Node):
    def __init__(self,
                 assignment,
                 action_var=None,
                 action_value=None,
                 tag=None,
                 identifier=None,
                 pai=None,
                 *args,
                 **kwargs):
        if tag == None:
            tag = "{}={}".format(action_var, action_value)
        if identifier == None:
            # identifier = "{}={}_from_{}".format(action_var, action_value, pai)
            identifier = "{}={}_from_{}".format(action_var, action_value, pai)

        # print("Creating Node {}".format(tag))
        super().__init__(tag=tag, identifier=identifier, *args, **kwargs)
        self.assignment = assignment  #state of the world
        self.action_var = action_var
        self.action_value = action_value
        self.count = 0


#then you can transition only the operating aircrafts
def transition_one_day(aircraft_state):
    pass


def monte_carlo_greedy(fleet_state, calendar):
    pass
    return schedule
