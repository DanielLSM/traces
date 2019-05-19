import numpy
import pandas as pd
from collections import OrderedDict, defaultdict

from tr.core.resources import f1_in, f2_out
from tr.core.parsers import excel_to_book, book_to_kwargs_MPO
from tr.core.common import FleetManagerBase
from tr.core.utils import advance_date, dates_between
from tr.core.csp import Variable, Assignment, Schedule
from tr.core.backtrack import solve_csp_schedule

import pulp as plp

checks = {
    'A_Initial': {
        'initial-days': 'DY-A',
        'initial-hours': 'FH-A',
        'initial-cycles': 'FC-A',
        'max-days': 'ACI-DY',
        'max-hours': 'ACI-FH',
        'max-cycles': 'ACI-FC'
    }
}


class SchedulerEDF(FleetManagerBase):
    """ Currently for A/C-Checks only, nodes are partial schedules and, tree as total schedules """

    def __init__(self, *args, **kwargs):
        FleetManagerBase.__init__(self, **kwargs)
        context = self._compute_inital_context()
        schedule_partial = self.generate_schedules_heuristic(context)
        global_schedule = OrderedDict()
        for aircraft in schedule_partial.keys():
            global_schedule[aircraft] = {}
            global_schedule[aircraft]['due_dates'] = []
            global_schedule[aircraft]['DY'] = []
            global_schedule[aircraft]['FH'] = []
            global_schedule[aircraft]['FC'] = []
            global_schedule[aircraft]['DY LOST'] = []
            global_schedule[aircraft]['FH LOST'] = []
            global_schedule[aircraft]['FC LOST'] = []

        while not self.is_context_done(context):
            csp_vars = self.cspify(context)
            schedule_partial = solve_csp_schedule(csp_vars)

            import ipdb
            ipdb.set_trace()
            # schedule_partial = self.generate_schedules_heuristic(context)
            # here we will call backtrack

            for aircraft in self.fleet.aircraft_info.keys():
                maxDY = self.fleet.aircraft_info[aircraft]['A_Initial'][
                    checks['A_Initial']['max-days']]
                maxFH = self.fleet.aircraft_info[aircraft]['A_Initial'][
                    checks['A_Initial']['max-hours']]
                maxFC = self.fleet.aircraft_info[aircraft]['A_Initial'][
                    checks['A_Initial']['max-cycles']]
                global_schedule[aircraft]['due_dates'].append(
                    schedule_partial[aircraft]['A_Initial']['due_date'])
                global_schedule[aircraft]['DY'].append(
                    maxDY -
                    schedule_partial[aircraft]['A_Initial']['waste'][0])
                global_schedule[aircraft]['FH'].append(
                    maxFH -
                    schedule_partial[aircraft]['A_Initial']['waste'][1])
                global_schedule[aircraft]['FC'].append(
                    maxFC -
                    schedule_partial[aircraft]['A_Initial']['waste'][2])
                global_schedule[aircraft]['DY LOST'].append(
                    schedule_partial[aircraft]['A_Initial']['waste'][0])
                global_schedule[aircraft]['FH LOST'].append(
                    schedule_partial[aircraft]['A_Initial']['waste'][1])
                global_schedule[aircraft]['FC LOST'].append(
                    schedule_partial[aircraft]['A_Initial']['waste'][2])
            context = self.compute_next_context(schedule_partial,
                                                self.end_date)

        self._save_to_xls(global_schedule)

    @staticmethod
    def _save_to_xls(global_schedule):
        dict1 = OrderedDict()
        dict1['Fleet'] = []
        dict1['A/C ID'] = []
        dict1['START'] = []
        dict1['END'] = []
        dict1['DY'] = []
        dict1['FH'] = []
        dict1['FC'] = []
        dict1['DY LOST'] = []
        dict1['FH LOST'] = []
        dict1['FC LOST'] = []
        i = 1
        for aircraft in global_schedule.keys():
            for _ in range(len(global_schedule[aircraft]['due_dates'])):
                dict1['Fleet'].append(aircraft[0:4])
                dict1['A/C ID'].append(aircraft[5:])
                dict1['START'].append(global_schedule[aircraft]['due_dates']
                                      [_].date().isoformat())
                dict1['END'].append(global_schedule[aircraft]['due_dates']
                                    [_].date().isoformat())
                dict1['DY'].append(global_schedule[aircraft]['DY'][_])
                dict1['FH'].append(global_schedule[aircraft]['FH'][_])
                dict1['FC'].append(global_schedule[aircraft]['FC'][_])
                dict1['DY LOST'].append(
                    global_schedule[aircraft]['DY LOST'][_])
                dict1['FH LOST'].append(
                    global_schedule[aircraft]['FH LOST'][_])
                dict1['FC LOST'].append(
                    global_schedule[aircraft]['FC LOST'][_])
                i += 1
        df = pd.DataFrame(dict1, columns=dict1.keys())

        print(df)
        df.to_excel('output.xlsx')
        # root = Tree()

    def cspify(self, context):
        #order vars by due date
        sorted_x = sorted(
            context.items(),
            key=lambda kv: kv[1]['A_Initial']['due_date'].timestamp(),
            reverse=True)
        sorted_dict = OrderedDict(sorted_x)

        ordered_vars = []
        for key in sorted_dict:
            start_date = sorted_dict[key]['A_Initial']['last_due_date']
            end_date = sorted_dict[key]['A_Initial']['due_date']
            domain = self.get_domain(start_date, end_date, key=key)
            var = Variable(name=key, domain=domain)
            ordered_vars.append(var)

        assignment = Assignment(ordered_vars)
        return assignment

    def get_max_slots(self, due_date):
        check_types = ['a-type', 'c-type']
        slots = [
            self.calendar.calendar[due_date]['resources']['slots'][check]
            for check in check_types
        ]
        max_slots = max(slots)
        return max_slots

    def get_domain(self, date_start, date_end, check_type='a-type', key=None):
        domain = []
        domain.append(date_start)
        due_date = date_start
        while due_date <= date_end:
            if self.calendar.calendar[due_date]['allowed'][
                    'public holidays'] and self.calendar.calendar[due_date][
                        'allowed']['a-type']:
                for _ in range(self.get_max_slots(due_date)):
                    domain.append(due_date)
            due_date = advance_date(due_date, days=int(1))
        return domain

    def is_context_done(self, context):
        for aircraft in context.keys():
            if context[aircraft]['A_Initial']['due_date'] > self.end_date:
                return True
        return False

    def generate_schedules_heuristic(self, context):
        """ generate schedules using an heuristic, in this case, will only
        generate one by considering one order, in reality, we could generate,
        up to 45!= 1.1962222e+56 XD, but we will generate a single node"""
        calendar = self.calendar.calendar
        schedule_partial = OrderedDict()
        for check in checks.keys():
            for aircraft in context.keys():
                schedule_partial[aircraft] = {}
                calendar, partial_schedule_aircraft = self.fill_in_calendar(
                    calendar, aircraft, context[aircraft]['A_Initial'])
                schedule_partial[aircraft][check] = partial_schedule_aircraft
        return schedule_partial

    def fill_in_calendar(self,
                         calendar,
                         aircraft,
                         context_aircraft,
                         check_type='a-type'):

        due_date = context_aircraft['due_date']
        waste = context_aircraft['waste']
        last_due_date = context_aircraft['last_due_date']
        while due_date >= last_due_date:
            if calendar[due_date]['allowed']['public holidays'] and calendar[
                    due_date]['allowed']['a-type']:
                if calendar[due_date]['resources']['slots'][check_type] >= 0:
                    calendar[due_date]['resources']['slots'][check_type] -= 1
                    context_aircraft['due_date'] = due_date
                    context_aircraft['waste'] = waste
                    return calendar, context_aircraft
                else:
                    month = due_date.month_name()[0:3]
                    due_date = advance_date(due_date, days=int(-1))
                    waste[0] += 1
                    waste[1] += self.fleet.aircraft_info[aircraft]['DFH'][
                        month]
                    waste[2] += self.fleet.aircraft_info[aircraft]['DFC'][
                        month]
                    # subtract here the timings
            else:
                month = due_date.month_name()[0:3]
                due_date = advance_date(due_date, days=int(-1))
                waste[0] += 1
                waste[1] += self.fleet.aircraft_info[aircraft]['DFH'][month]
                waste[2] += self.fleet.aircraft_info[aircraft]['DFC'][month]

        import ipdb
        ipdb.set_trace()
        print("ERROR: IMPOSSIBLE SCHEDULE")
        return calendar, 'IMPOSSIBLE'

    def _compute_inital_context(self):
        due_dates = OrderedDict()
        for check in checks.keys():
            for aircraft in self.fleet.aircraft_info.keys():
                DY_i = self.fleet.aircraft_info[aircraft][check][
                    checks[check]['initial-days']]
                FH_i = self.fleet.aircraft_info[aircraft][check][
                    checks[check]['initial-hours']]
                FC_i = self.fleet.aircraft_info[aircraft][check][
                    checks[check]['initial-cycles']]
                maxDY = self.fleet.aircraft_info[aircraft][check][checks[check]
                                                                  ['max-days']]
                maxFH = self.fleet.aircraft_info[aircraft][check][
                    checks[check]['max-hours']]
                maxFC = self.fleet.aircraft_info[aircraft][check][
                    checks[check]['max-cycles']]
                due_dates[aircraft] = {}
                due_dates[aircraft][check] = {}
                due_dates[aircraft][check]['due_date'], due_dates[aircraft][
                    check]['waste'], due_dates[aircraft][check][
                        'last_due_date'] = self.compute_next_due_date(
                            self.start_date,
                            self.end_date,
                            aircraft,
                            DY_i=DY_i,
                            FH_i=FH_i,
                            FC_i=FC_i,
                            maxDY=maxDY,
                            maxFH=maxFH,
                            maxFC=maxFC)
        return due_dates  #this is the context, e.g, next_due_dates

    def compute_next_context(self,
                             schedule_partial,
                             end_date,
                             check_type='A_Initial'):
        """ Given start_due_dates for all the fleet, and an end_date, assign a schedule
        this is similar to solving a MILP  """
        for check in checks.keys():
            for aircraft in schedule_partial.keys():
                maxDY = self.fleet.aircraft_info[aircraft][check][checks[check]
                                                                  ['max-days']]
                maxFH = self.fleet.aircraft_info[aircraft][check][
                    checks[check]['max-hours']]
                maxFC = self.fleet.aircraft_info[aircraft][check][
                    checks[check]['max-cycles']]
                schedule_partial[aircraft][check][
                    'due_date'], schedule_partial[aircraft][check][
                        'waste'], schedule_partial[aircraft][check][
                            'last_due_date'] = self.compute_next_due_date(
                                schedule_partial[aircraft]['A_Initial']
                                ['due_date'],
                                end_date,
                                aircraft,
                                maxDY=maxDY,
                                maxFH=maxFH,
                                maxFC=maxFC)
        return schedule_partial  #this is the context, e.g, next_due_dates

    def compute_next_due_date(self,
                              start_date,
                              end_date,
                              aircraft,
                              DY_i=0,
                              FH_i=0,
                              FC_i=0,
                              maxDY=0,
                              maxFH=0,
                              maxFC=0):
        DY, FH, FC = DY_i, FH_i, FC_i

        due_date = start_date
        month = start_date.month_name()[0:3]
        maxDY_proxy = maxDY - 1
        maxFH_proxy = maxFH - self.fleet.aircraft_info[aircraft]['DFH'][month]
        maxFC_proxy = maxFC - self.fleet.aircraft_info[aircraft]['DFC'][month]

        while DY <= maxDY_proxy and FH <= maxFH_proxy and FC <= maxFC_proxy:
            month = due_date.month_name()[0:3]
            DY += 1
            FH += self.fleet.aircraft_info[aircraft]['DFH'][month]
            FC += self.fleet.aircraft_info[aircraft]['DFC'][month]
            self.fleet.aircraft_info[aircraft]['DFH'][month]

            due_date = advance_date(due_date, days=int(1))

        waste = [maxDY - DY, maxFH - FH, maxFC - FC]
        return due_date, waste, start_date


if __name__ == '__main__':

    import time
    t = time.time()
    book = excel_to_book(f1_in)
    kwargs = book_to_kwargs_MPO(book)
    scheduler = SchedulerEDF(**kwargs)
    print("INFO: total elapsed time {} seconds".format(time.time() - t))
