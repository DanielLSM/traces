import pandas as pd
import random
from reals.core.resources import f1_in, f2_out
from reals.core.utils import dict_to_list, diff_time_list, get_slots
from reals.core.utils import advance_date

from collections import OrderedDict, defaultdict

# collection of APIs from in and out of python


def excel_to_book(file_input: str):
    try:
        book = pd.read_excel(file_input,
                             sheet_name=None)  # returns an ordered dict
    except Exception as e:
        print(e)
        print('Error parsing the excel file into a dict book buddy!')
    return book


def book_to_kwargs_MPO(book):
    print("#########################")
    print("INFO: building from xlsx")
    """ given an MPO input, compute dict where keys are aircraft ids and the rest 
    of sheet info is organized by aircraft id """
    aircraft_info = get_aircraft_info_MPO(book)
    calendar_restrictions = get_restrictions_MPO(book)

    # each type of maintenance as several restrictions we will devide in 2
    # time and hangar restrictions
    m_type_restriction = {}
    m_type_restriction = {'time_type': 'day'}

    a_time = dict_to_list(calendar_restrictions['A_Not_Allowed']['Dates'])
    c_time = diff_time_list(calendar_restrictions['C_Not_Allowed'])
    all_time = dict_to_list(calendar_restrictions['Public_Holidays']['Dates'])

    a_resources = {'slots': get_slots(calendar_restrictions['More_A_Slots'])}
    c_resources = {'slots': get_slots(calendar_restrictions['More_C_Slots'])}

    m_type_restriction['a-type'] = {'time': a_time, 'resources': a_resources}
    m_type_restriction['c-type'] = {'time': c_time, 'resources': c_resources}
    m_type_restriction['all'] = {'time': all_time}

    # TODO
    start_date = pd.to_datetime(book['Additional'][2017][1])
    end_date = advance_date(start_date, years=6)

    m_type_restriction['start_date'] = start_date
    m_type_restriction['end_date'] = end_date

    # # all these restrictions will restrict the general calendar
    # # for
    print("INFO: information from xlsx parsed with success")
    print("#########################")

    return {
        'aircraft_info': aircraft_info,
        'restrictions': m_type_restriction,
    }


def get_restrictions_MPO(book):

    print('INFO: gathering restrictions info')
    restrictions_info = OrderedDict()
    for sheet_name in book.keys():
        if 'Aircraft ID' not in book[sheet_name].keys():
            for column_idx in book[sheet_name].keys():
                restrictions_info[sheet_name] = book[sheet_name].to_dict()

    print('INFO: restrictions info completed')
    return restrictions_info


def get_aircraft_info_MPO(book):
    print('INFO: gathering aircraft info')

    aircraft_info = OrderedDict()
    for sheet_name in book.keys():
        if 'Aircraft ID' in book[sheet_name].keys():
            # create ordered dict to store aircraft info
            for _ in range(len(book[sheet_name]['Aircraft ID'])):
                a_id = book[sheet_name]['Aircraft ID'][_]
                if a_id not in list(aircraft_info.keys()):
                    aircraft_info[a_id] = OrderedDict()
                if sheet_name not in list(aircraft_info[a_id].keys()):
                    aircraft_info[a_id][sheet_name] = OrderedDict()

            # fill the info of other columns, pandas already adds idx to equal
            # value columns
            for column_idx in book[sheet_name].keys():
                if column_idx != 'Aircraft ID':
                    for _ in range(len(book[sheet_name]['Aircraft ID'])):
                        a_id = book[sheet_name]['Aircraft ID'][_]
                        aircraft_info[a_id][sheet_name][column_idx] = book[
                            sheet_name][column_idx][_]

    print('INFO: aircraft info completed')
    return aircraft_info


if __name__ == '__main__':
    try:
        book = excel_to_book(f1_in)
    except Exception as e:
        raise e

    kwargs = book_to_kwargs_MPO(book)
