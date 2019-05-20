import random
from copy import deepcopy


class Constraint:
    def __init__(self, info, *args, **kwargs):
        self._info = info

    def satisfied(self, assignment):
        raise NotImplementedError

    def consistent(self, assignment):
        raise NotImplementedError

    def relies_on(self):
        raise NotImplementedError


class Variable:
    def __init__(self, name, domain, info=None, *args, **kwargs):
        self.name = name
        self.domain = domain
        self._info = info

    def get_info(self):
        return self._info


class Assignment:
    def __init__(self, variables=[], *args, **kwargs):

        self.vars = variables
        self.unassigned_vars = [var.name for var in variables]
        self.assignment = {var.name: None for var in variables}
        self.vars_domain = {var.name: var.domain for var in variables}

    def assign(self, var_name, value):
        try:
            assert var_name in self.unassigned_vars, "var already assigned"
        except:
            import ipdb
            ipdb.set_trace()
        # self.unassigned_vars.remove(var)  #pop
        # print("NOT NODE:var:{}, value:{}".format(var_name, value))
        self.unassigned_vars.pop()
        self.assignment[var_name] = value
        self.vars_domain[var_name] = value

    def get_value(self, var):
        return self.assignment[var]

    def get_domain(self, var):
        return self.vars_domain[var]

    def restrict_domain(self, var, dom):
        self.vars_domain[var] = dom

    def __len__(self):
        return len(list(self.assignment.keys()))


class Schedule(Assignment):
    def __init__(self, vars, *args, **kwargs):
        super().__init__(self, vars, *args)

    def assign(self, var, value):
        super().assign(var, value)
        self.unassigned_vars.pop()

    #TODO lets do the processing here
    def order_var_earliest_due_date(self):
        pass

    #TODO this is naturally done when building the domain!
    def order_domain_due_date(self):
        pass

    def render(self):
        raise NotImplementedError


class CSP:
    def __init__(self, vars=[], constraints=None, *args, **kwargs):

        self.vars = vars
        self.constraints = constraints  #maps vars to constraints
        if self.constraints:
            self.vars_constraints = {var: [] for var in self.vars}

    #we can make an yield on this one
    def select_next_var(self, assignment):
        return random.choice(assignment.vars)

    #we can make an yield on this one
    def select_next_value(self, assignment, var):
        return random.choice(assignment.vars_domain[var])

    def variable_constraints(self, variable):
        assert self.vars_constraints[variable] == 0

        for constraint in self.constraints:
            constraint_vars = constraint.relies_on()
            if variable in constraint_vars:
                self.vars_constraints[variable].add(constraint)

    def change_domain(self, assignment, var):
        domain = assignment.get_domain(var)
        assert len(domain) != 0
        return domain

    def satisfied_assignment(self, assignment):
        assert len(self.vars) == len(assignment.vars), "variables mismatch"
        if len(assignment.unassigned) == 0:
            return True

        # for constraint in self.constraints:
        #     if not constraint.satisfied():
        #         return False
        return False

    def consistent_assignment(self, assignment, var):
        for constraint in self.constraints:
            if not constraint.consistent_assignment:
                return False
        return True


class CSPSchedule:
    def __init__(self, vars=[], constraints=None, *args, **kwargs):

        self.vars = vars

    def do_next_assignment(self, assignment, variable, value):

        next_assignment = deepcopy(assignment)
        next_assignment.assign(variable, value)
        next_assignment = self.arc_consistency(next_assignment, value)
        return next_assignment

    def arc_consistency(self, assignment, value):
        for var_name in assignment.unassigned_vars:
            if value in assignment.vars_domain[var_name]:
                assignment.vars_domain[var_name].remove(value)
            if len(assignment.vars_domain[var_name]) == 0:
                return None
        return assignment

    def satisfied_assignment(self, assignment):
        assert len(self.vars) == len(assignment.vars), "variables mismatch"
        if len(assignment.unassigned_vars) == 0:
            return True
        return False

    def variable_ordering_heuristic(self, schedule_assign):
        return schedule_assign.unassigned_vars[-1]

    def value_ordering_heuristic(self, schedule_assign, var):
        # return schedule_assign.vars_domain[var]  #schedule by early date
        return schedule_assign.vars_domain[var][::-1]  #schedule by due date

    def select_next_var(self, schedule_assign):
        return self.variable_ordering_heuristic(schedule_assign)

    def select_next_values(self, schedule_assign, var):
        return self.value_ordering_heuristic(schedule_assign, var)


if __name__ == "__main__":
    print("hello")
