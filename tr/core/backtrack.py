# https://github.com/jonalloub/Iterative-Deepening-Search-5-Puzzle/blob/master/SearchAgent.py
from tr.core.csp import CSPSchedule, Variable, Constraint, Schedule
from tr.core.tree import NodeX, NodeSchedule
from treelib import Tree


class BacktrackSchedule:
    def __init__(self, csp, start_assign, *args, **kwargs):
        assert isinstance(csp, CSPSchedule), "problem is not CSP"
        assert isinstance(start_assign, Schedule), "assignment is not valid"
        self.csp = csp
        self.start_assign = start_assign

    #TODO
    def solve(self, schedule_assign):
        if self.csp.satisfied_assignment(schedule_assign):
            return schedule_assign

        var = self.csp.select_next_var(schedule_assign)
        if not var: return None

        value = self.csp.select_next_value(schedule_assign, var)


class BacktrackTreeDFS:
    def __init__(self, csp, start_assign, *args, **kwargs):
        assert isinstance(csp, CSPSchedule), "problem is not CSP"
        assert isinstance(start_assign, Schedule), "assignment is not valid"
        self.csp = csp
        # self.start_assign = start_assign
        self.root = Node(start_assign)

    def solve(self, node_schedule):
        if self.csp.satisfied_assignment(node_schedule.assignment):
            return node_schedule

        next_var = self.csp.select_next_var(node_schedule.assignment)
        if next_var == None:
            return None

        # here when we expand the childs, we need to fix domain
        for child in node_schedule.expand_no_heuristic(
                self.csp, node_schedule.assignment, next_var):
            next_node = self.solve(child)

            return next_node

        var = self.csp.select_next_var(node_schedule.assignment)
        if not var: return None

        value = self.csp.select_next_value(node_schedule.assignment, var)


class BacktrackTreelib:
    def __init__(self, csp, start_assign, *args, **kwargs):
        assert isinstance(csp, CSPSchedule), "problem is not CSP"
        assert isinstance(start_assign, Schedule), "assignment is not valid"
        self.csp = csp
        # self.start_assign = start_assign
        self.tree = Tree()
        self.root = self.tree("Root", "root", data={})

    def solve(self, node_schedule):
        if self.csp.satisfied_assignment(node_schedule.assignment):
            return node_schedule.assignment

        next_var = self.csp.select_next_var(node_schedule.assignment)
        if next_var == None:
            return None

        # here when we expand the childs, we need to fix domain
        for child in node_schedule.expand_with_heuristic(
                self.csp, node_schedule.assignment, next_var):
            self.tree[node_schedule].count += 1
            self.tree.add_node(child, node_schedule)
            next_node = self.solve(child)

            return None

        # var = self.csp.select_next_var(node_schedule.schedule_assign)
        # if not var: return None

        # value = self.csp.select_next_value(node_schedule.schedule_assign, var)


if __name__ == "__main__":
    # csp = CSPSchedule
    # print("put sad wings around me now")

    # bb = BacktrackSchedule()
    from treelib import Node, Tree
    tree = Tree()
    root = tree.create_node(1, 1, data={})
    node = NodeX("lul", 2, 2)
    tree.add_node(node, root)
