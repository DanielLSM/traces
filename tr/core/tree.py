# Welcome to the first tree-search implementation for CSP's on the internet
from tr.core.csp import CSPSchedule, Variable, Constraint, Schedule
import treelib


class NodeX(treelib.Node):
    def __init__(self, assignment, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assignment = assignment


class NodeSchedule(treelib.Node):
    def __init__(self,
                 assignment,
                 action_var=None,
                 action_value=None,
                 tag=None,
                 identifier=None,
                 *args,
                 **kwargs):
        if tag == None:
            self.tag = "{}={}".format(action_var, action_value)
        if identifier == None:
            self.identifier = "{}={}".format(action_var, action_value)
        super().__init__(tag=tag, identifier=identifier, *args, **kwargs)
        self.assignment = assignment  #state of the world
        self.action_var = action_var
        self.action_value = action_value
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
        childs = []
        for action_value in csp.select_next_values(assignment, action_var):
            child = self.child_node(csp, assignment, action_var, action_value)
            if child != None:
                childs.append(child)
        return

    def child_node(self, csp, assignment, action_var, action_value):
        next_assignment = csp.do_next_assignment(assignment, action_var,
                                                 action_value)
        if next_assignment != None:
            return NodeSchedule(next_assignment, self, action_var,
                                action_value)
        return None


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
