# https://github.com/jonalloub/Iterative-Deepening-Search-5-Puzzle/blob/master/SearchAgent.py
# part of old API of solving the problem as a CSP
from tr.core.csp import CSPSchedule, Variable, Constraint, Schedule, Assignment
from tr.core.tree import NodeSchedule
from tr.core.csp import CSPSchedule
from collections import OrderedDict, defaultdict
from treelib import Tree


def all_unique_domains(csp_vars):
    vars_domain = csp_vars.vars_domain
    vars_domain_feasibility_dict = OrderedDict()
    all_domains = []
    for var in vars_domain.keys():
        all_domains.extend(vars_domain[var])

    all_unique_domains = list(set(all_domains))
    # import ipdb
    # ipdb.set_trace()
    return all_unique_domains


def csp_lowest_cardinalities(csp_vars):
    vars_domain = csp_vars.vars_domain
    vars_domain_feasibility_dict = OrderedDict()
    for var in vars_domain.keys():
        assert var not in vars_domain_feasibility_dict.keys()
        vars_domain_feasibility_dict[var] = OrderedDict()
        vars_domain_set = set(vars_domain[var])
        for value in vars_domain_set:
            vars_domain_feasibility_dict[var][value] = vars_domain[var].count(value)
            assert vars_domain_feasibility_dict[var][value] != 0
    # dates per counts
    inverse_feasibility_dict = OrderedDict()
    for var in vars_domain_feasibility_dict.keys():
        for value in vars_domain_feasibility_dict[var]:
            counter = vars_domain_feasibility_dict[var][value]
            if value not in inverse_feasibility_dict.keys():
                inverse_feasibility_dict[value] = counter
                continue
            inverse_feasibility_dict[value] = max(inverse_feasibility_dict[value], counter)

    lowest_cardinalities = []
    for timestamp in inverse_feasibility_dict.keys():
        if inverse_feasibility_dict[timestamp] == 1:
            lowest_cardinalities.append(timestamp)

    return lowest_cardinalities


def check_feasibility(csp_vars):
    # import ipdb; ipdb.set_trace()
    vars_domain = csp_vars.vars_domain
    vars_domain_feasibility_dict = OrderedDict()
    for var in vars_domain.keys():
        assert var not in vars_domain_feasibility_dict.keys()
        vars_domain_feasibility_dict[var] = OrderedDict()
        vars_domain_set = set(vars_domain[var])
        for value in vars_domain_set:
            vars_domain_feasibility_dict[var][value] = vars_domain[var].count(value)
            assert vars_domain_feasibility_dict[var][value] != 0

# dates per counts
    inverse_feasibility_dict = OrderedDict()
    for var in vars_domain_feasibility_dict.keys():
        for value in vars_domain_feasibility_dict[var]:
            counter = vars_domain_feasibility_dict[var][value]
            if value not in inverse_feasibility_dict.keys():
                inverse_feasibility_dict[value] = counter
                continue
            inverse_feasibility_dict[value] = max(inverse_feasibility_dict[value], counter)

    full_domain_cardinality = 0
    variables_cardinality = len(vars_domain_feasibility_dict)
    for value in inverse_feasibility_dict.keys():
        full_domain_cardinality += inverse_feasibility_dict[value]

    try:
        feasibility = (full_domain_cardinality >= variables_cardinality)
        assert feasibility
    except:
        import ipdb
        ipdb.set_trace()

    import ipdb
    ipdb.set_trace()

    return feasibility


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
        for child in node_schedule.expand_with_heuristic(self.csp, node_schedule, next_var):
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


if __name__ == "__main__":
    pass