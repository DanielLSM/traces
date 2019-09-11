# So we are going to solve the task packaging problem as a bin packaging problem.
# Each day is a bin and we can compute à priori all the bins and their limits in man-hours
# for A checks is trivial and we keep assigining until limits are reached
# for C checks, when a C check starts, bins are created each day, then ordered
# the order of the bins is: fill the ones with least amount of aircrafts assigned first
from tr.core.utils import advance_date, save_pickle, load_pickle


class TasksPlanner:
    def __init__(self, aircraft_tasks, df_tasks, skills, skills_ratios_A,
                 skills_ratios_C, man_hours):
        self.aircraft_tasks = aircraft_tasks
        self.df_tasks = df_tasks
        self.skills = skills
        self.skills_ratios_A = skills_ratios_A
        self.skills_ratios_C = skills_ratios_C
        self.man_hours = man_hours

        try:
            self.final_calendar = {}
            self.final_fleet_schedule = {}
            self.final_calendar['A'] = load_pickle("calendar_A.pkl")
            self.final_calendar['C'] = load_pickle("calendar_C.pkl")

            # TODO you need to include the merged A to C checks, its kinda  important to know
            # which ones are merged lol
            self.final_fleet_schedule['A'] = load_pickle(
                "final_schedule_A.pkl")
            self.final_fleet_schedule['C'] = load_pickle(
                "final_schedule_C.pkl")
        except:
            import ipdb
            ipdb.set_trace()

        import ipdb
        ipdb.set_trace()

    def solve_tasks(self):
        pass


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
