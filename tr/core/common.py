import numpy
import pandas as pd
import time
from collections import OrderedDict, defaultdict

# from tr.core.resources import f1_in, f2_out
from tr.core.parsers import book_to_kwargs_MPO
from tr.core.utils import advance_date, dates_between

from tr.core.utils import save_pickle, load_pickle

#TODO: you can read the readme.md, but the basic idea is,
# for a_checks, we put 1 everywehre, then we put 2 on more_a_slots
# the a_not_allowed already restricts fridays and weekends

# for c_checks, we put 3 everywhre, then we restrict the callendar,
# by putting different keys in the allowed which will be acessed later,
# one key for c_peak, another c_not_allowed, because c_peaks and c_not_allowed
# are a lot of days, we block all those days, and then restrict the weekends
# at the end.

# for the a slots, they are directly replaced, for the c slots most slots are
# on c_peak or c_not_allowed days, so we need to unblock when adding the slots
# but again, restrict the weekends at the end always


def get_calendar(start_date, end_date, type='days'):
    n_days = dates_between(start_date, end_date, type='days')
    calendar = OrderedDict()
    for _ in range(n_days + 1):
        calendar[advance_date(start_date, days=_)] = {
            'allowed': {
                'public holidays': True,
                'no_weekends': True,
                'a-type': True,
                'c-type': True,
                'c_allowed': True,
                'c_peak': True
            },
            'resources': {
                'slots': {
                    'a-type': 1,
                    'c-type': 3,
                }
            }
        }
    return calendar


class Calendar:
    def __init__(self, *args, **kwargs):
        self.time_type = kwargs['time_type']
        self.start_date = kwargs['start_date']
        self.end_date = kwargs['end_date']
        self.a_type = kwargs['a-type']
        self.c_type = kwargs['c-type']
        self.public_holidays = kwargs['all']

        print("#########################")
        print("INFO: setting up initial calendar")
        calendar = get_calendar(self.start_date, self.end_date, type='days')
        print("INFO: adding public holidays")
        calendar = self.restrict_calendar(calendar,
                                          self.public_holidays['time'],
                                          info='public holidays')

        print("INFO: adding a-type calendar restrictions")
        calendar = self.restrict_calendar(calendar, self.a_type['time'], info='a-type')

        print("INFO: adding c-type calendar restrictions")
        calendar = self.restrict_calendar(calendar, self.c_type['time'], info='c-type')
        calendar = self.restrict_calendar(calendar, self.c_type['c_allowed'], info='c_allowed')
        calendar = self.restrict_calendar(calendar, self.c_type['c_peak'], info='c_peak')

        print("INFO: adding a-type resources (slots)")
        calendar = self.add_resources(calendar,
                                      self.a_type['resources'],
                                      typek='slots',
                                      info='a-type')

        print("INFO: adding c-type resources (slots)")
        calendar = self.add_resources(calendar,
                                      self.c_type['resources'],
                                      typek='slots',
                                      info='c-type')
        calendar = self.add_resources(calendar,
                                      self.c_type['resources'],
                                      typek='slots',
                                      info='c_allowed')
        calendar = self.add_resources(calendar,
                                      self.c_type['resources'],
                                      typek='slots',
                                      info='c_peak')

        calendar = self.restrict_weekends(calendar)
        print("#########################")
        self.calendar = calendar
        print("INFO: calendar complete!")
        # self.test()

    @staticmethod
    def restrict_calendar(calendar, restrict_list, info='not allowed'):
        start_date = list(calendar.keys())[0]
        end_date = list(calendar.keys())[-1]

        for _ in restrict_list:
            if _ > start_date and _ < end_date:
                calendar[_]['allowed'][info] = False
        return calendar

    @staticmethod
    def add_resources(calendar, restrict_dict, typek='slots', info='a-type'):
        start_date = list(calendar.keys())[0]
        end_date = list(calendar.keys())[-1]
        for _ in restrict_dict[typek].keys():
            if _ > start_date and _ < end_date:
                calendar[_]['resources'][typek][info] = restrict_dict['slots'][_]
                calendar[_]['allowed'][info] = True
        return calendar

    def restrict_weekends(self, calendar):
        start_date = list(calendar.keys())[0]
        end_date = list(calendar.keys())[-1]
        n_days = dates_between(start_date, end_date, type='days')
        for _ in range(n_days + 1):
            day = advance_date(start_date, days=_)
            if day.weekday() >= 5:
                calendar[day]['allowed']['a-type'] = False
                calendar[day]['allowed']['c-type'] = False
                calendar[day]['allowed']['c_allowed'] = False
                calendar[day]['allowed']['c_peak'] = False
                calendar[day]['allowed']['no_weekends'] = False
        return calendar

    def test(self):
        iso_str = '6/3/2019'
        daterinos = pd.to_datetime(iso_str, format='%m/%d/%Y')
        import ipdb
        ipdb.set_trace()
        assert self.calendar[daterinos]['allowed']['c-type'] == False
        assert self.calendar[daterinos]['allowed']['c_allowed'] == False
        assert self.calendar[daterinos]['allowed']['c_peak'] == False
        assert self.calendar[daterinos]['allowed']['no_weekends'] == False
        assert self.calendar[daterinos]['resources']['slots']['c-type'] == 1

    def plan(self, time_window):
        pass

    def reset_calendar(self):
        pass

    def render(self):
        pass  # something something tkinter?


class Fleet:
    def __init__(self, start_date, end_date, *args, **kwargs):

        self.start_date = start_date
        self.end_date = end_date
        self.aircraft_info = kwargs

    def due_dates_from_info(self, start_date, end_date):
        due_dates = OrderedDict()
        time0 = time.time()
        for aircraft in self.aircraft_info.keys():
            due_dates[aircraft] = {
                'a-type': self.compute_due_dates_type_a(start_date, end_date, aircraft),
                'c-type': self.compute_due_dates_type_c(start_date, end_date, aircraft)
            }
            print("INFO: due dates of aircraft {} globally forecasted ELAPSED TIME {}".format(
                aircraft,
                time.time() - time0))

        return due_dates

    def compute_due_date_type_a(self, start_date, end_date, aircraft):
        DY_i = self.aircraft_info[aircraft]['A_INITIAL']['DY-A']
        FH_i = self.aircraft_info[aircraft]['A_INITIAL']['FH-A']
        FC_i = self.aircraft_info[aircraft]['A_INITIAL']['FC-A']
        maxDY = self.aircraft_info[aircraft]['A_INITIAL']['ACI-DY']
        maxFH = self.aircraft_info[aircraft]['A_INITIAL']['ACI-FH']
        maxFC = self.aircraft_info[aircraft]['A_INITIAL']['ACI-FC']
        due_date = self.compute_next_due_date(aircraft,
                                              start_date,
                                              DY_i=DY_i,
                                              FH_i=FH_i,
                                              FC_i=FC_i,
                                              maxDY=maxDY,
                                              maxFH=maxFH,
                                              maxFC=maxFC)
        if due_date >= end_date:
            due_date = None
        return due_date

    def compute_due_date_type_c(self, start_date, end_date, aircraft):
        DY_i = self.aircraft_info[aircraft]['C_Initial']['DY-C']
        FH_i = self.aircraft_info[aircraft]['C_Initial']['FH-C']
        FC_i = self.aircraft_info[aircraft]['C_Initial']['FC-C']
        maxDY = self.aircraft_info[aircraft]['C_Initial']['CCI-DY']
        maxFH = self.aircraft_info[aircraft]['C_Initial']['CCI-FH']
        maxFC = self.aircraft_info[aircraft]['C_Initial']['CCI-FC']
        due_date = self.compute_next_due_date(aircraft,
                                              start_date,
                                              DY_i=DY_i,
                                              FH_i=FH_i,
                                              FC_i=FC_i,
                                              maxDY=maxDY,
                                              maxFH=maxFH,
                                              maxFC=maxFC)
        if due_date >= end_date:
            due_date = None
        return due_date

    #this was made purely for computacional speed, one less if every comp
    def compute_next_due_date(self,
                              aircraft,
                              last_due_date=0,
                              DY_i=0,
                              FH_i=0,
                              FC_i=0,
                              maxDY=0,
                              maxFH=0,
                              maxFC=0):
        DY, FH, FC = DY_i, FH_i, FC_i
        try:
            due_date = advance_date(last_due_date, DY)
        except:
            import ipdb
            ipdb.set_trace()
        while DY <= maxDY and FH <= maxFH and FC <= maxFC:
            month = last_due_date.month_name()[0:3]
            DY += 1
            FH += self.aircraft_info[aircraft]['DFH'][month]
            FC += self.aircraft_info[aircraft]['DFC'][month]
        due_date = advance_date(due_date, days=int(DY))
        return due_date

    def compute_due_dates_type_a(self, start_date, end_date, aircraft):
        due_dates = []
        last_due_date = start_date
        DY_i = self.aircraft_info[aircraft]['A_INITIAL']['DY-A']
        FH_i = self.aircraft_info[aircraft]['A_INITIAL']['FH-A']
        FC_i = self.aircraft_info[aircraft]['A_INITIAL']['FC-A']
        maxDY = self.aircraft_info[aircraft]['A_INITIAL']['ACI-DY']
        maxFH = self.aircraft_info[aircraft]['A_INITIAL']['ACI-FH']
        maxFC = self.aircraft_info[aircraft]['A_INITIAL']['ACI-FC']
        due_date = self.compute_next_due_date(aircraft,
                                              last_due_date,
                                              DY_i=DY_i,
                                              FH_i=FH_i,
                                              FC_i=FC_i,
                                              maxDY=maxDY,
                                              maxFH=maxFH,
                                              maxFC=maxFC)
        if due_date <= end_date:
            due_dates.append(due_date)
        while due_date <= end_date:
            due_date = self.compute_next_due_date(aircraft,
                                                  due_date,
                                                  maxDY=maxDY,
                                                  maxFH=maxFH,
                                                  maxFC=maxFC)
            if due_date < end_date:
                due_dates.append(due_date)
        return due_dates

    def compute_due_dates_type_c(self, start_date, end_date, aircraft):
        due_dates = []
        last_due_date = start_date
        DY_i = self.aircraft_info[aircraft]['C_Initial']['DY-C']
        FH_i = self.aircraft_info[aircraft]['C_Initial']['FH-C']
        FC_i = self.aircraft_info[aircraft]['C_Initial']['FC-C']
        maxDY = self.aircraft_info[aircraft]['C_Initial']['CCI-DY']
        maxFH = self.aircraft_info[aircraft]['C_Initial']['CCI-FH']
        maxFC = self.aircraft_info[aircraft]['C_Initial']['CCI-FC']
        due_date = self.compute_next_due_date(aircraft,
                                              last_due_date,
                                              DY_i=DY_i,
                                              FH_i=FH_i,
                                              FC_i=FC_i,
                                              maxDY=maxDY,
                                              maxFH=maxFH,
                                              maxFC=maxFC)
        if due_date <= end_date:
            due_dates.append(due_date)
        while due_date <= end_date:
            due_date = self.compute_next_due_date(aircraft,
                                                  due_date,
                                                  maxDY=maxDY,
                                                  maxFH=maxFH,
                                                  maxFC=maxFC)
            if due_date < end_date:
                due_dates.append(due_date)
        return due_dates


# this should be an abc abstract class
class FleetManagerBase:
    def __init__(self, *args, **kwargs):

        self.calendar = Calendar(**kwargs['restrictions'])
        self.start_date = self.calendar.start_date
        self.end_date = self.calendar.end_date
        self.fleet = Fleet(start_date=self.start_date,
                           end_date=self.end_date,
                           **kwargs['aircraft_info'])

        if 'aircraft_tasks' in kwargs.keys():
            self.aircraft_tasks = kwargs['aircraft_tasks']
            self.df_tasks = kwargs['df_tasks']
            self.skills = kwargs['skills']
            self.skills_ratios_A = kwargs['skills_ratios_A']
            self.skills_ratios_C = kwargs['skills_ratios_C']
            self.man_hours = kwargs['man_hours']
            self.delivery_date = kwargs['delivery date']
            save_pickle(self.aircraft_tasks, 'aircraft_tasks.pkl')
            save_pickle(self.df_tasks, 'df_tasks.pkl')
            save_pickle(self.skills, 'skills.pkl')
            save_pickle(self.skills_ratios_A, 'skills_ratios_A.pkl')
            save_pickle(self.skills_ratios_C, 'skills_ratios_C.pkl')
            save_pickle(self.man_hours, 'man_hours.pkl')
            save_pickle(self.delivery_date, 'delivery_date.pkl')
        else:
            self.aircraft_tasks = load_pickle('aircraft_tasks.pkl')
            self.df_tasks = load_pickle('df_tasks.pkl')
            self.skills = load_pickle('skills.pkl')
            self.skills_ratios_A = load_pickle('skills_ratios_A.pkl')
            self.skills_ratios_C = load_pickle('skills_ratios_C.pkl')
            self.man_hours = load_pickle('man_hours.pkl')
            self.delivery_date = load_pickle('delivery_date.pkl')

        # self.kwargs_c_checks = kwargs['c-checks']
        # self.kwargs_c_checks_days = kwargs['c-checks-days']


if __name__ == '__main__':
    import time
    time0 = time.time()
    from tr.core.parsers import excel_to_book
    try:
        book = excel_to_book(f1_in)
    except Exception as e:
        print('you messed up')
        raise e

    kwargs = book_to_kwargs_MPO(book)
    fmb = FleetManagerBase(**kwargs)
    fmb.fleet.due_dates_from_info(fmb.calendar.start_date, fmb.calendar.end_date)
    # print('INFO: TOTAL TIME ELAPSED: {}'.format(time.time() - time0))
