import random


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
    def __init__(self, domain, info, *args, **kwargs):
        self.domain = domain
        self._info = info

    def get_info(self):
        return self._info


class Assignment:
    def __init__(self, vars, *args, **kwargs):
        self.vars = vars
        self.unassigned_vars = vars
        self.assignment = dict.fromkeys(vars)
        self.vars_domain = {var: var.domain for var in vars}

    def assign(self, var, value):
        assert var in self.unassigned_vars, "var already assigned"
        self.unassigned_vars.remove(var)  #pop
        self.assignment[var] = value
        self.vars_domain[var] = value

    def get_value(self, var):
        return self.assignment[var]

    def get_domain(self, var):
        return self.vars_domain[var]

    def restrict_domain(self, var, dom):
        self.vars_domain[var] = dom

    def __len__(self):
        return len(list(self.assignment.keys()))


class Schedule(Assignment):
    def __init__(self, vars, due_dates, *args, **kwargs):
        super().__init__(self, vars, *args)
        self.due_dates = due_dates
        self.ordered_vars = self.order_var_earliest_due_date()
        self.ordered_domain = self.order_domain_due_date()

    def assign(self, var, value):
        super().assign(var, value)
        self.ordered_vars.pop()

    #TODO lets do the processing here
    def order_var_earliest_due_date(self):
        ordered_vars = self.vars
        return ordered_vars

    #TODO this is naturally done when building the domain
    def order_domain_due_date(self):
        return self.vars_domain

    def render(self):
        raise NotImplementedError


class CSP:
    def __init__(self, vars, constraints, *args, **kwargs):
        self.vars = vars
        self.constraints = constraints  #maps vars to constraints
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
        assert len(self.vars) == len(assignment), "variables mismatch"
        for constraint in self.constraints:
            if not constraint.satisfied():
                return False
        return True

    def consistent_assignment(self, assignment, var):
        for constraint in self.constraints:
            if not constraint.consistent_assignment:
                return False
        return True


class CSPSchedule(CSP):
    def __init__(self, vars, domains, constraints, *args, **kwargs):
        super().__init__(self, vars, domains, constraints)

    def do_next_assignment(self, assignment, variable, value):
        assignment.assign(variable, value)
        next_assignment = self.arc_consistency(assignment, value)
        return next_assignment

    def arc_consistency(self, assignment, value):
        for var in assignment.unassigned:
            assignment.vars_domain[var].remove(value)
        return assignment

    #order by shortest due_date
    #it helps if variables are ordered already
    def variable_ordering_heuristic(self, schedule_assign):
        return schedule_assign.unassigned[-1]

    #order by value closest to due_date
    #it helps if domains are ordered already
    def value_ordering_heuristic(self, schedule_assign, var):
        value = 0
        return value

    def select_next_var(self, schedule_assign):
        return self.variable_ordering_heuristic(schedule_assign)

    def select_next_value(self, schedule_assign, var):
        return self.value_ordering_heuristic(schedule_assign, var)


if __name__ == "__main__":
    print("hello")
