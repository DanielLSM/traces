import yaml
import os, sys

from tr.core.resources import f1_in_checks, f1_in_tasks
from tr.core.utils import save_pickle, load_pickle
from tr.core.parsers import book_to_kwargs, excel_to_book


def read_yaml(yaml_path):
    import yaml
    # Read YAML file
    try:
        with open(yaml_path, 'r') as stream:
            config_file = yaml.safe_load(stream)
    except e as Exception:
        raise (e)
    return config_file


def build_fast_exec_file():
    if not os.path.exists("build"):
        os.makedirs("build")
        os.makedirs("build/input_files")
        os.makedirs("build/check_files")
        os.makedirs("build/tasks_files")
        os.makedirs("build/output_files")
    if not os.path.exists("check_planning")
        os.makedirs("check_planning")
    if not os.path.exists("task_planning")
        os.makedirs("task_planning")
    try:
        book_checks = excel_to_book(f1_in_checks)
        book_tasks = excel_to_book(f1_in_tasks)
    except Exception as e:
        raise e
    kwargs = book_to_kwargs(book_checks, book_tasks)
    save_pickle(kwargs, "build/input_files/fast_exec.pkl")
