#OLD CSP implementation
# Welcome to the first tree-search implementation for CSP's on the internet
from tr.core.csp import CSPSchedule, Variable, Constraint, Schedule
import treelib


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

    # def __repr__(self):
    #     return "Node {}".format(self.tag)

    # we need to fix domain here
    def expand_no_heuristic(self, csp, assignment, action_var):
        return [
            self.child_node(csp, assignment, action_var, action_value)
            for action_value in assignment.vars_domain[action_var]
        ]

    def expand_with_heuristic(self, csp, node_schedule, action_var):
        childs = []
        for action_value in csp.select_next_values(node_schedule.assignment, action_var):
            child = self.child_node(csp, node_schedule, action_var, action_value)
            if child != None and len(childs) == 0:
                childs.append(child)
            elif child != None and child.tag != childs[-1].tag:
                childs.append(child)

        # aux = [child.tag for child in childs]
        # import ipdb
        # ipdb.set_trace()
        return childs

    def child_node(self, csp, node_schedule, action_var, action_value):
        next_assignment = csp.do_next_assignment(node_schedule.assignment, action_var, action_value)
        if next_assignment != None:
            return NodeSchedule(next_assignment,
                                action_var=action_var,
                                action_value=action_value,
                                pai=node_schedule.identifier)
        return None