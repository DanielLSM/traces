# Welcome to the first tree-search implementation for CSP's on the internet
from tr.core.csp import CSPSchedule, Variable, Constraint, Schedule
import treelib


class NodeX(treelib.Node):
    def __init__(self, assignment, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assignment = assignment


class NodeSchedule(treelib.Node):
    def __init__(self, assignment, action_var, action_value, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assignment = assignment  #state of the world
        self.action_var = action_var
        self.action_value = action_value
        self.tag = "{}={}".format(action_var, action_value)
        self.count = 0
        #parent is passed on *args

    def __repr__(self):
        return "Node {}".format(self.tag)

    # we need to fix domain here
    def expand_no_heuristic(self, csp, assignment, action_var):
        return [
            self.child_node(csp, assignment, action_var, action_value)
            for action_value in assignment.vars_domain[action_var]
        ]

    def expand_with_heuristic(self, csp, assignment, action_var):
        return [
            self.child_node(csp, assignment, action_var, action_value)
            for action_value in csp.select_next_value(assignment, action_var)
        ]

    def child_node(self, csp, assignment, action_var, action_value):
        next_assignment = csp.do_next_assignment(assignment, action_var,
                                                 action_value)
        return NodeSchedule(next_assignment, self, action_var, action_value)


class NodeExample:
    def __init__(self,
                 assignment,
                 parent=None,
                 action_var=None,
                 action_value=None):
        self.assignment = assignment  #state of the world
        self.parent = parent
        self.action_var = action_var
        self.action_value = action_value

    def __repr__(self):
        return "Node {}={}".format(self.action_var, self.action_value)

    # we need to fix domain here
    def expand_no_heuristic(self, csp, assignment, action_var):
        return [
            self.child_node(csp, assignment, action_var, action_value)
            for action_value in assignment.vars_domain[action_var]
        ]

    def child_node(self, csp, assignment, action_var, action_value):
        next_assignment = csp.do_next_assignment(assignment, action_var,
                                                 action_value)
        return NodeExample(next_assignment, self, action_var, action_value)
