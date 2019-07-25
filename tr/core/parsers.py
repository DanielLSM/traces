import pandas as pd
import random
import datetime
from tqdm import tqdm

from tr.core.resources import f1_in, f2_out, f1_in_tasks
from tr.core.utils import dict_to_list, diff_time_list, get_slots
from tr.core.utils import advance_date

from collections import OrderedDict, defaultdict

# collection of APIs from in and out of python


def excel_to_book(file_input: str):
    print("INFO: parsing xlsx to runtime book")
    try:
        book = pd.read_excel(file_input,
                             sheet_name=None)  # returns an ordered dict
    except Exception as e:
        print(e)
        print('Error parsing the excel file into a dict book buddy!')
    print("INFO: xlsx to runtime book completed")
    return book


def book_to_kwargs_MPO(book):
    print("#########################")
    print("INFO: processing from runtime book")
    """ given an MPO input, compute dict where keys are aircraft ids and the rest 
    of sheet info is organized by aircraft id """
    aircraft_info = get_aircraft_info_MPO(book)
    calendar_restrictions = get_restrictions_MPO(book)

    # each type of maintenance as several restrictions we will devide in 2
    # time and hangar restrictions
    m_type_restriction = {}
    m_type_restriction = {'time_type': 'day'}

    a_time = dict_to_list(calendar_restrictions['A_NOT_ALLOWED']['DATE'])
    c_time = diff_time_list(calendar_restrictions['C_NOT_ALLOWED'])
    all_time = dict_to_list(calendar_restrictions['PUBLIC_HOLIDAYS']['DATE'])

    a_resources = {'slots': get_slots(calendar_restrictions['MORE_A_SLOTS'])}
    c_resources = {'slots': get_slots(calendar_restrictions['MORE_C_SLOTS'])}

    m_type_restriction['a-type'] = {'time': a_time, 'resources': a_resources}
    m_type_restriction['c-type'] = {'time': c_time, 'resources': c_resources}
    m_type_restriction['all'] = {'time': all_time}

    # TODO
    end = datetime.datetime(2022, 2, 1, 0, 0)
    start_date = pd.to_datetime(book['ADDITIONAL'][2019][1])
    end_date = pd.to_datetime(end)

    m_type_restriction['start_date'] = start_date
    m_type_restriction['end_date'] = end_date

    # # all these restrictions will restrict the general calendar
    # # for
    print("INFO: information from runtime parsed with success")
    print("#########################")

    return {
        'aircraft_info': aircraft_info,
        'restrictions': m_type_restriction,
    }


def get_restrictions_MPO(book):

    print('INFO: gathering restrictions info')
    restrictions_info = OrderedDict()
    for sheet_name in book.keys():
        if 'A/C TAIL' not in book[sheet_name].keys():
            for column_idx in book[sheet_name].keys():
                restrictions_info[sheet_name] = book[sheet_name].to_dict()

    print('INFO: restrictions info completed')
    return restrictions_info


def get_aircraft_info_MPO(book):
    print('INFO: gathering aircraft info')

    aircraft_info = OrderedDict()
    for sheet_name in book.keys():
        if 'A/C TAIL' in book[sheet_name].keys():
            # create ordered dict to store aircraft info
            for _ in range(len(book[sheet_name]['A/C TAIL'])):
                a_id = book[sheet_name]['A/C TAIL'][_]
                if a_id not in list(aircraft_info.keys()):
                    aircraft_info[a_id] = OrderedDict()
                if sheet_name not in list(aircraft_info[a_id].keys()):
                    aircraft_info[a_id][sheet_name] = OrderedDict()

            # fill the info of other columns, pandas already adds idx to equal
            # value columns
            for column_idx in book[sheet_name].keys():
                if column_idx != 'A/C TAIL':
                    for _ in range(len(book[sheet_name]['A/C TAIL'])):
                        a_id = book[sheet_name]['A/C TAIL'][_]
                        aircraft_info[a_id][sheet_name][column_idx] = book[
                            sheet_name][column_idx][_]

    print('INFO: aircraft info completed')
    return aircraft_info


def book_to_kwargs_tasks(book, aircrafts):
    print("#########################")
    print("INFO: processing from runtime book")
    """ given an MPO input, compute dict where keys are aircraft ids and the rest 
    of sheet info is organized by aircraft id """
    aircraft_tasks = OrderedDict()
    for _ in aircrafts:
        aircraft_tasks[_] = OrderedDict()

    sheet_name = 'TASK_LIST'
    df = book[sheet_name]
    import ipdb
    for _ in df.keys():
        df[_] = df[_].apply(lambda x: x.strip() if type(x) is str else x)

    # df = df[df['TASK BY BLOCK'] != 'LINE MAINTENANCE']

    df = df.reset_index(drop=True)
    # ipdb.set_trace()
    assert 'A/C' in df.keys()
    # import ipdb
    # ipdb.set_trace()
    # maps aircrafts, to items, to task number (unique indentifier) to stuffs, I think it makes sense,
    # but we should also return the df for searching purposes!
    for line_idx in tqdm(range(len(df['A/C']))):
        aircraft = df['A/C'][line_idx]
        item = df['ITEM'][line_idx]
        if item not in aircraft_tasks[aircraft].keys():
            aircraft_tasks[aircraft][item] = OrderedDict()
            aircraft_tasks[aircraft][item]['assignments'] = []
        aircraft_tasks[aircraft][item][line_idx] = OrderedDict()
        for column_idx in df.keys():
            if column_idx != 'A/C' and column_idx != 'ITEM':
                value = df[column_idx][line_idx]
                aircraft_tasks[aircraft][item][line_idx][column_idx] = value

    print("INFO: information from runtime parsed with success")
    print("#########################")

    return {'aircraft_tasks': aircraft_tasks, 'df': df}


if __name__ == '__main__':
    try:
        f1_in = "~/local-dev/traces/resources/Check Scheduling Input.xlsx"
        book = excel_to_book(f1_in)
    except Exception as e:
        raise e

    kwargs = book_to_kwargs_MPO(book)
    aircrafts = kwargs['aircraft_info'].keys()
    try:
        book = excel_to_book(f1_in_tasks)
    except Exception as e:
        raise e
    kwargs_tasks = book_to_kwargs_tasks(book, aircrafts)
    import ipdb
    ipdb.set_trace()
