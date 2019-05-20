# https://github.com/jonalloub/Iterative-Deepening-Search-5-Puzzle/blob/master/SearchAgent.py
from tr.core.csp import CSPSchedule, Variable, Constraint, Schedule, Assignment
from tr.core.tree import NodeSchedule
from tr.core.csp import CSPSchedule
from treelib import Tree


class BacktrackTreelib:
    def __init__(self, csp, start_assign, *args, **kwargs):
        assert isinstance(csp, CSPSchedule), "problem is not CSP"
        assert isinstance(start_assign, Assignment), "assignment is not valid"
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
                print("BACKTRACKKKKKKKK")

            self.tree.add_node(child, node_schedule)
            # print("Depth:{}".format(self.tree.depth()))

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


if __name__ == "__main__":
    pass