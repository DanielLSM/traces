import numpy
import pandas as pd
from collections import OrderedDict, defaultdict

from reals import f1_in, f2_out
from reals.core.parser import excel_to_book, book_to_kwargs_MPO
from reals.core.schedule_classes import FleetManagerBase
from reals.core.utils import advance_date, dates_between
# from reals.core.tree import Tree

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
            schedule_partial = self.generate_schedules_heuristic(context)
            import ipdb
            ipdb.set_trace()
            schedule_partial = self.generate_schedules_MILP(context)
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

    # def generate_schedules_MILP(self, context):
    #     """ Instead of using that simple heuristic, we now use a MILP,
    #     build a MILP, solve a MILP, standard stuff """
    #     print('INFO: starting local MILP')
    #     aircrafts = list(context.keys())
    #     import ipdb
    #     ipdb.set_trace()
    #     schedule_partial = OrderedDict()

    #     #variables to optimize, let us say, binary for the restrictions, aircraft and date
    #     for aircraft in aircrafts:
    #         last_due_date = context[aircraft]['A_Initial']['last_due_date']
    #         due_date = context[aircraft]['A_Initial']['due_date']
    #         while last_due_date <= due_date:

    #             last_due_date = advance_date(due_date, days=int(1))

    #     #constraints hangar and due date, hangar constraints are made with callendar
    #     calendar = self.calendar.calendar

    #     #objective function, minimize sum of days to due date

    #     print('INFO: local MILP solved')
    #     #post procesing
    #     # several nodes? #TODO
    #     return schedule_partial

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
        # here the bug for reference
        # due_date = advance_date(start_date, days=int(DY))
        due_date = start_date
        month = start_date.month_name()[0:3]
        maxDY_proxy = maxDY - 1
        maxFH_proxy = maxFH - self.fleet.aircraft_info[aircraft]['DFH'][month]
        maxFC_proxy = maxFC - self.fleet.aircraft_info[aircraft]['DFC'][month]

        # maxDY_proxy = maxDY
        # maxFH_proxy = maxFH
        # maxFC_proxy = maxFC

        while DY <= maxDY_proxy and FH <= maxFH_proxy and FC <= maxFC_proxy:
            month = due_date.month_name()[0:3]
            # print(month)
            DY += 1
            FH += self.fleet.aircraft_info[aircraft]['DFH'][month]
            FC += self.fleet.aircraft_info[aircraft]['DFC'][month]
            self.fleet.aircraft_info[aircraft]['DFH'][month]
            # print(due_date)
            due_date = advance_date(due_date, days=int(1))

            #TODO utilization is same every day lol
        # due_date = advance_date(due_date, days=int(DY - DY_i))
        waste = [maxDY - DY, maxFH - FH, maxFC - FC]
        # bug for reference
        # start_date = advance_date(start_date, days=int(DY_i))
        return due_date, waste, start_date


if __name__ == '__main__':

    import time
    t = time.time()
    book = excel_to_book(f1_in)
    kwargs = book_to_kwargs_MPO(book)
    scheduler = SchedulerEDF(**kwargs)
    print("INFO: total elapsed time {} seconds".format(time.time() - t))
