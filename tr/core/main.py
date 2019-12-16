import yaml
import argparse
from termcolor import colored
from tr.core.helpers import read_yaml, build_fast_exec_file
from tr.core.utils import load_pickle
from tr.core.edf import SchedulerEDF
VERSION = 1.0

print(
    colored(
        '''
  _____           __  __              _____      _____      __        __ 
 |  __ \         |  \/  |     /\     |  __ \    |  __ \    / /       /_ |
 | |__) |   ___  | \  / |    /  \    | |__) |   | |  | |  / /_        | |
 |  _  /   / _ \ | |\/| |   / /\ \   |  ___/    | |  | | | '_ \       | |
 | | \ \  |  __/ | |  | |  / ____ \  | |        | |__| | | (_) |  _   | |
 |_|  \_\  \___| |_|  |_| /_/    \_\ |_|        |_____/   \___/  (_)  |_|
                                                                         
                                                      
                                                      
                                                      ''', "blue"))

parser = argparse.ArgumentParser()
parser.add_argument("-v", "--version", help="show program version")
parser.add_argument("-cf",
                    "--config",
                    help="configuration file",
                    default="../config.yaml",
                    type=str)
parser.add_argument("-pc",
                    "--pre_compute",
                    help="pre computes files for faster runs",
                    default=False,
                    type=bool)
parser.add_argument("-r",
                    "--run",
                    help="run scheduler according to the configuration file",
                    default=True,
                    type=bool)

args = parser.parse_args()
if args.version:
    print("current version {}".format(VERSION))
if args.pre_compute:
    build_fast_exec_file()

if args.run:
    config_file = read_yaml(args.config)
    kwargs = load_pickle("build/input_files/fast_exec.pkl")
    kwargs.update({"config_params": config_file["parameters"]})
    scheduler = SchedulerEDF(**kwargs)

    if config_file['process']['c-checks']:
        scheduler.plan_by_days("C")

    if config_file['process']['a-checks']:
        scheduler.plan_by_days("A")

    if config_file['process']['tasks']:
        scheduler.plan_tasks_fleet()

    if config_file['process']['save_checks_to_excel']:
        try:
            final_schedule_a = load_pickle(
                "build/check_files/final_schedule_A.pkl")
            final_schedule_c = load_pickle(
                "build/check_files/final_schedule_C.pkl")
            scheduler.optimizer_checks.final_schedule_to_excel(
                final_schedule_a, type_check="A")
            scheduler.optimizer_checks.final_schedule_to_excel(
                final_schedule_c, type_check="C")
        except:
            raise "Process checks first before saving!"

    if config_file['process']['save_tasks_to_excel']:
        try:
            scheduler.optimizer_tasks.task_calendar_to_excel()
        except:
            raise "Process tasks first before saving!"

    print("INFO: processing complete according to config file")
