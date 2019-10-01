# So we are going to solve the task packaging problem as a bin packaging problem.
# Each day is a bin and we can compute à priori all the bins and their limits in man-hours
# for A checks is trivial and we keep assigining until limits are reached
# for C checks, when a C check starts, bins are created each day, then ordered
# the order of the bins is: fill the ones with least amount of aircrafts assigned first
import numpy as np
import pandas as pd

from datetime import datetime
from collections import OrderedDict

from tr.core.utils import advance_date, save_pickle, load_pickle


class TasksPlanner:
    def __init__(self, aircraft_tasks, aircraft_info, df_tasks, skills, skills_ratios_A,
                 skills_ratios_C, man_hours, delivery):
        self.aircraft_tasks = aircraft_tasks
        self.aircraft_info = aircraft_info
        self.df_tasks = df_tasks
        self.skills = skills
        self.skills_ratios_A = skills_ratios_A
        self.skills_ratios_C = skills_ratios_C
        self.man_hours = man_hours
        self.delivery = delivery

        try:
            self.final_calendar = {}
            self.final_fleet_schedule = {}
            self.final_calendar['A'] = load_pickle("calendar_A.pkl")
            self.final_calendar['C'] = load_pickle("calendar_C.pkl")

            # TODO you need to include the merged A to C checks, its kinda  important to know
            # which ones are merged lol
            self.final_fleet_schedule['A'] = load_pickle("final_schedule_A.pkl")
            self.final_fleet_schedule['C'] = load_pickle("final_schedule_C.pkl")
        except:
            import ipdb
            ipdb.set_trace()

        self.processed_aircraft_tasks = self._process_aircraft_tasks()

        import ipdb
        ipdb.set_trace()

    def solve_tasks(self):
        pass

    def _process_aircraft_tasks(self):
        processed_aircraft_tasks = OrderedDict()
        for aircraft in self.aircraft_tasks.keys():
            self.simulate_lifetime(aircraft)
        return processed_aircraft_tasks

    def simulate_lifetime(self, aircraft):
        dfh = self.aircraft_info[aircraft]['DFH']
        dfc = self.aircraft_info[aircraft]['DFC']
        index_ac = np.where(self.delivery['A/C TAIL'] == aircraft)[0][0]
        delivery_date = self.delivery['DELIVERY DATE'][index_ac].date()
        end_date = advance_date(delivery_date, years=50)
        date_range = pd.date_range(delivery_date, end_date)
        simulated_lifetime = np.zeros((7, len(date_range)))
        simulated_lifetime[0, :] = date_range
        a_checks_dates = list(self.final_fleet_schedule['A'][aircraft].keys())
        c_checks_dates = list(self.final_fleet_schedule['C'][aircraft].keys())
        c_checks_dates_end = []

        for c_check_date in c_checks_dates:
            real_tat = self.final_fleet_schedule['C'][aircraft][c_check_date]['STATE']['TAT']
            c_checks_dates_end.append(advance_date(c_checks_dates, days=real_tat))

        fh, fc = 0, 0
        for _ in range(len(date_range)):
            if simulated_lifetime[0, _] in a_checks_dates:
                simulated_lifetime[5, i] = 1

            for k in range(len(a_checks_dates)):
                if c_checks_dates[k] <= simulated_lifetime[0, i] <= c_checks_dates:
                    simulated_lifetime[6, i]

            if simulated_lifetime[5, i] or simulated_lifetime[6, i]:
                simulated_lifetime[1, i] = np.round(fh, decimals=2)
                simulated_lifetime[2, i] = np.round(fc, decimals=2)

            #TODO: start counting those days baby

        import ipdb
        ipdb.set_trace()
        month = (due_date.month_name()[0:3]).upper()
        # temp = temp.date()


class TaskBin:
    def __init__(self, dates, skills, fill_ratio):
        self.dates = dates

        pass

    # merges 2 bins and outputs a bin
    @staticmethod
    def merge_bins():
        pass

    # mostly for c_checks
    @staticmethod
    def order_bins():
        pass
