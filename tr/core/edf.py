import numpy
import pandas as pd
from tqdm import tqdm
import pulp as plp
import time
import operator

from collections import OrderedDict, defaultdict

from tr.core.parsers import excel_to_book, book_to_kwargs
from tr.core.common import FleetManagerBase
from tr.core.utils import advance_date, dates_between, save_pickle, load_pickle
from tr.core.utils import convert_iso_to_timestamp
from tr.core.csp import Variable, Assignment, Schedule
from tr.core.backtrack import solve_csp_schedule, check_feasibility, csp_lowest_cardinalities
from tr.core.backtrack import csp_lowest_cardinalities, all_unique_domains
from tr.core.tree_search import TreeDaysPlanner
from tr.core.tasks_planner import TasksPlanner

checks = {
    'A_INITIAL': {
        'initial-days': 'DY-A',
        'initial-hours': 'FH-A',
        'initial-cycles': 'FC-A',
        'max-days': 'A-CI-DY',
        'max-hours': 'A-CI-FH',
        'max-cycles': 'A-CI-FC'
    }
}


class SchedulerEDF(FleetManagerBase):
    """ Currently for A/C-Checks only, nodes are partial schedules and, 
    tree as total schedules """
    def __init__(self, *args, **kwargs):
        FleetManagerBase.__init__(self, **kwargs)

        iso_str = '01/10/2020'
        daterinos = pd.to_datetime(iso_str, format='%m/%d/%Y')
        self.calendar.calendar[daterinos]['resources']['slots']['a-type'] += 1

        self.optimizer_checks = TreeDaysPlanner(self.calendar, self.fleet)
        self.optimizer_tasks = TasksPlanner(self.aircraft_tasks, self.fleet.aircraft_info,
                                            self.df_tasks, self.skills, self.skills_ratios_A,
                                            self.skills_ratios_C, self.man_hours,
                                            self.delivery_date, self.df_aircraft_shaved)

    def plan_by_days(self, check_type="C"):
        self.optimizer_checks.solve_schedule(check_type)

    def plan_tasks_fleet(self):
        self.optimizer_tasks.solve_tasks()
