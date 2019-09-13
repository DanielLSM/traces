import pandas as pd
import numpy as np
import random
import datetime
from tqdm import tqdm

from tr.core.resources import f2_out, f1_in_tasks, f1_in_checks
from tr.core.utils import dict_to_list, diff_time_list, get_slots, diff_time_list_peak_season
from tr.core.utils import advance_date, days_between_dates, convert_iso_to_timestamp

from collections import OrderedDict, defaultdict


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


# Function 4: Given a string checks if it is a Month/Year or day.
# Returns time in months if it was a 'Y' or 'M', otherwise 0 is returned.
def preprocessMonths(x):
    # that, if x is a string,
    if type(x) is str:
        if x[-1] == 'M':
            return float(x[0:len(x) - 2])
        elif x[-1] == 'Y':
            return float(x[0:len(x) - 2]) * 12
        else:
            return 0
    else:
        return


# Function 5: Given a string checks if it is a day
# Return amount of days if it was a 'D', otherwise 0 is returned
def preprocessDays(x):
    # that, if x is a string,
    if type(x) is str:
        if x[-1] == 'D':
            return float(x[0:len(x) - 2])
        else:
            return 0
    else:
        return


# Function that changes everything unequal to 0 to 1 necessary for tasks by block columns
def preprocesstask(x):
    # that, if x is a string,
    if type(x) is str:
        return 1


def book_to_kwargs_MPO(book):
    print("#########################")
    print("INFO: processing from runtime checks book")
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
    c_peak = diff_time_list_peak_season(calendar_restrictions['C_PEAK'])
    all_time = dict_to_list(calendar_restrictions['PUBLIC_HOLIDAYS']['DATE'])

    a_resources = {'slots': get_slots(calendar_restrictions['MORE_A_SLOTS'])}
    c_resources = {'slots': get_slots(calendar_restrictions['MORE_C_SLOTS'])}

    m_type_restriction['a-type'] = {'time': a_time, 'resources': a_resources}
    m_type_restriction['c-type'] = {
        'time': c_time,
        'resources': c_resources,
        'c_peak': c_peak,
        'c_allowed': c_time
    }
    m_type_restriction['all'] = {'time': all_time}

    end = datetime.datetime(2023, 1, 1, 0, 0)
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
            # for column_idx in book[sheet_name].keys():
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


def book_to_kwargs_tasks(book):
    print("#########################")
    print("INFO: processing from runtime tasks book")
    # given an MPO input, compute dict where keys are
    # aircraft ids and the rest of sheet info is organized by aircraft id

    sheet_name = 'TASK_LIST'
    df = book[sheet_name]

    # equivalent to Preprocess.py/PreprocessTasks
    def process_df(df):
        for _ in df.keys():
            df[_] = df[_].apply(lambda x: x.strip() if type(x) is str else x)
        df['PER FH'].fillna(False, inplace=True)
        df['PER FC'].fillna(False, inplace=True)
        df['LIMIT FH'].fillna(False, inplace=True)
        df['LIMIT FC'].fillna(False, inplace=True)
        df['LIMIT EXEC DT'].fillna(False, inplace=True)
        df['LAST EXEC FC'].fillna(False, inplace=True)
        df['LAST EXEC FH'].fillna(False, inplace=True)
        df['LAST EXEC DT'].fillna(False, inplace=True)
        df['PER CALEND'].fillna(False, inplace=True)
        df['TASK BY BLOCK'].fillna("C-CHECK", inplace=True)
        # do not use things without due dates
        # df = df[(df['PER FH'] != False) | (df['PER FC'] != False) |
        #         (df['PER CALEND'] != False)]
        df = df[df['TASK BY BLOCK'] != 'LINE MAINTENANCE']
        df = df.reset_index(drop=True)
        return df

    df = process_df(df)

    assert 'A/C' in df.keys()
    # maps aircrafts, to items, to task number (unique indentifier) to stuffs,
    # I think it makes sense,
    # but we should also return the df for searching purposes!
    aircraft_tasks = OrderedDict()
    for _ in df['A/C'].unique():
        aircraft_tasks[_] = OrderedDict()

    skills = []
    for _ in book['SKILL_TYPE']['SKILL TYPE']:
        skills.append(_)

    skills_ratios_A = OrderedDict()
    for _ in book['A-CHECK_NRS_RATIO']['SKILL GI']:
        skills_ratios_A[_] = {}

    skills_ratios_C = OrderedDict()
    for _ in book['C-CHECK_NRS_RATIO']['SKILL GI']:
        skills_ratios_C[_] = {}

    for _ in book['A-CHECK_NRS_RATIO']['SKILL GI'].keys():
        skill = book['A-CHECK_NRS_RATIO']['SKILL GI'][_]
        skill_block = book['A-CHECK_NRS_RATIO']['BLOCK'][_]
        skill_modifier = book['A-CHECK_NRS_RATIO']['SKILL MDO'][_]
        skill_ratio = book['A-CHECK_NRS_RATIO']['RATIO'][_]

        if skill_block not in skills_ratios_A[skill].keys():
            skills_ratios_A[skill][skill_block] = {}
        skills_ratios_A[skill][skill_block][skill_modifier] = skill_ratio

    for _ in book['C-CHECK_NRS_RATIO']['SKILL GI'].keys():
        skill = book['C-CHECK_NRS_RATIO']['SKILL GI'][_]
        skill_block = book['C-CHECK_NRS_RATIO']['BLOCK'][_]
        skill_modifier = book['C-CHECK_NRS_RATIO']['SKILL MDO'][_]
        skill_ratio = book['C-CHECK_NRS_RATIO']['RATIO'][_]

        if skill_block not in skills_ratios_C[skill].keys():
            skills_ratios_C[skill][skill_block] = {}
        skills_ratios_C[skill][skill_block][skill_modifier] = skill_ratio

    def get_man_hours(book):
        df_personnel = book['NUMBER_OF_TECHNICIANS']
        weekdays = df_personnel['Weekday'].unique()
        man_personnel = OrderedDict()
        #0=Monday, 1=Tuesday, this is nice for.. .weekday()
        ctx = 0
        for weekday in weekdays:
            man_personnel[ctx] = OrderedDict()
            for m_key in df_personnel.keys():
                if m_key != 'Weekday' and m_key != 'Week Number' and m_key != 'Date':
                    man_personnel[ctx][m_key] = np.mean(df_personnel[m_key][
                        df_personnel['Weekday'] == weekday])
            ctx += 1

        return man_personnel

    # for _ in book['NUMBER_OF_TECHNICIANS']['Date'].keys():
    #     date = book['NUMBER_OF_TECHNICIANS']['Date'][_]
    #     man_hours[date] = {}
    #     for key in book['NUMBER_OF_TECHNICIANS'].keys():
    #         if key != 'Weekday' and key != 'Week Number' and key != 'Date':
    #             man_hours[date][
    #                 key] = book['NUMBER_OF_TECHNICIANS'][key][_] * 8

    # for _ in range(2, 6):
    #     for date in man_hours.keys():
    #         new_date = advance_date(date, years=_)
    #         man_hours_skills[new_date] = man_hours[date]
    man_personnel = get_man_hours(book)
    man_hours_skills = OrderedDict()

    def shred_tasks(df_aircraft):
        ##### Preprocess data
        #### Excel file 1 maintenance tasks

        ###1. Modification/expanding dataset section

        ##Modification/expanding 1: nan values to zero
        #Replace nan values with zero in the PER FH and PER FC columns
        df_aircraft["PER FH"] = df_aircraft["PER FH"].fillna(0)
        df_aircraft["PER FC"] = df_aircraft["PER FC"].fillna(0)
        df_aircraft["PER CALEND"] = df_aircraft["PER CALEND"].fillna(0)
        # df_aircraft["TASK BY BLOCK"] = df_aircraft["TASK BY BLOCK"].apply(
        #     preprocesstask).fillna(0)

        ##Modification/expanding 2: new columns added for month and day
        #The CAL column needs a special treatment. The years are transformed to months.
        #Two new columns will be created: PER Month (only months and years (expressed in months))
        #and PER DAY (only in days!)
        df_aircraft['PER MONTH'] = df_aircraft['PER CALEND'].apply(
            preprocessMonths).fillna(0)
        df_aircraft['PER DAY'] = df_aircraft['PER CALEND'].apply(
            preprocessDays).fillna(0)

        ##Modification/expanding 3: new column with nr task added to dataset
        #Each of the tasks will be represented by a task nr starting from 0.
        #This can be found in the column 'NR TASK'
        df_aircraft['NR TASK'] = range(len(df_aircraft))

        ##Modification/expanding 4: Remove list that have no given limit in FH/FC/CALEND
        #The tasks that have no PER FH, PER FC, PER CALEND will be removed from the tasks list.
        tasks_no_date = np.where(
            (df_aircraft['PER FH'] + df_aircraft['PER FC'] +
             df_aircraft['PER MONTH'] + df_aircraft['PER DAY']) == 0)
        amount_remove = np.count_nonzero(tasks_no_date)
        index_labels = []
        for i in range(len(tasks_no_date[0])):
            index_labels.append(tasks_no_date[0][i])

        #Now dropping the rows without due dates
        df_aircraft = df_aircraft.drop(df_aircraft.index[index_labels])
        return df_aircraft, tasks_no_date, index_labels, amount_remove

    for aircraft in aircraft_tasks.keys():
        df_aircraft = df.copy(deep=True)
        df_aircraft = df_aircraft[df_aircraft['A/C'] == aircraft]
        df_aircraft = df_aircraft.reset_index(drop=True)
        df_aircraft, tasks_no_date, index_labels, amount_remove = shred_tasks(
            df_aircraft)

        for line_idx in list(df_aircraft.index):
            item = df_aircraft['ITEM'][line_idx]
            if item not in aircraft_tasks[aircraft].keys():
                aircraft_tasks[aircraft][item] = OrderedDict()
            aircraft_tasks[aircraft][item][line_idx] = OrderedDict()
            for column_idx in df_aircraft.keys():
                if column_idx != 'A/C' and column_idx != 'ITEM':
                    value = df_aircraft[column_idx][line_idx]
                    aircraft_tasks[aircraft][item][line_idx][
                        column_idx] = value

            # task by block 1: A-check, 0 C-check
            if aircraft_tasks[aircraft][item][line_idx][
                    'TASK BY BLOCK'] == "A-CHECK":
                main_skill = aircraft_tasks[aircraft][item][line_idx]['SKILL']
                block = aircraft_tasks[aircraft][item][line_idx]['BLOCK']
                man_hours_time = aircraft_tasks[aircraft][item][line_idx][
                    'Mxh EST.']
                aircraft_tasks[aircraft][item][line_idx]['SKILL'] = {}
                aircraft_tasks[aircraft][item][line_idx]['SKILL'][
                    main_skill] = man_hours_time

                if main_skill in skills_ratios_A.keys():
                    for extra_skill in skills_ratios_A[main_skill][block].keys(
                    ):
                        if main_skill != extra_skill:
                            aircraft_tasks[aircraft][item][line_idx]['SKILL'][
                                extra_skill] = 0
                    for extra_skill in skills_ratios_A.keys():
                        aircraft_tasks[aircraft][item][line_idx]['SKILL'][
                            extra_skill] = man_hours_time * skills_ratios_A[
                                extra_skill][block]

                import ipdb
                ipdb.set_trace()

            elif aircraft_tasks[aircraft][item][line_idx][
                    'TASK BY BLOCK'] == "C-CHECK":
                pass

    # for line_idx in tqdm(range(len(df['A/C']))):

    #     aircraft = df['A/C'][line_idx]
    #     item = df['ITEM'][line_idx]
    #     if item not in aircraft_tasks[aircraft].keys():
    #         aircraft_tasks[aircraft][item] = OrderedDict()
    #         aircraft_tasks[aircraft][item]['assignments'] = []
    #     aircraft_tasks[aircraft][item][line_idx] = OrderedDict()
    #     for column_idx in df.keys():
    #         if column_idx != 'A/C' and column_idx != 'ITEM':
    #             value = df[column_idx][line_idx]
    #             aircraft_tasks[aircraft][item][line_idx][column_idx] = value

    # # add a_check_items for now
    # for aircraft in aircraft_tasks.keys():
    #     a_checks_idxs = df[(df['TASK BY BLOCK'] == 'A-CHECK')
    #                        & (df['A/C'] == aircraft)].index.values.astype(int)
    #     a_checks_items = df['ITEM'][a_checks_idxs].unique()
    #     aircraft_tasks[aircraft]['a_checks_items'] = a_checks_items.tolist()

    print("INFO: information from runtime parsed with success")
    print("#########################")

    return {
        'aircraft_tasks': aircraft_tasks,
        'df_tasks': df,
        'skills': skills,
        'skills_ratios_A': skills_ratios_A,
        'skills_ratios_C': skills_ratios_C,
        'man_hours': man_hours_skills
    }


def book_to_kwargs_output(book_output):
    dfc = book_output['C-CHECK LIST']
    aircrafts = (dfc['A/C TAIL'].unique()).tolist()
    c_checks = OrderedDict()
    c_checks_days = OrderedDict()

    for _ in aircrafts:
        c_checks[_] = OrderedDict()
        c_checks_days[_] = []

    for idx in range(len(dfc['A/C TAIL'])):
        aircraft = dfc['A/C TAIL'][idx]
        c_check_code = dfc['CHECK'][idx]
        start_day = convert_iso_to_timestamp(dfc['START'][idx])
        end_day = convert_iso_to_timestamp(dfc['END'][idx])
        days = days_between_dates(start_day, end_day)
        assert c_check_code not in c_checks[aircraft].keys()
        c_checks[aircraft][c_check_code] = days
        c_checks_days[aircraft].extend(days)
        # import ipdb
        # ipdb.set_trace()
    return {'c-checks': c_checks, 'c-checks-days': c_checks_days}


def book_to_kwargs(book_checks, book_tasks=0, book_output=0):
    kwargs = book_to_kwargs_MPO(book_checks)
    if book_tasks != 0:
        kwargs_tasks = book_to_kwargs_tasks(book_tasks)
        kwargs.update(kwargs_tasks)
    # kwargs_output = book_to_kwargs_output(book_output)
    # kwargs.update(kwargs_output)
    return kwargs


if __name__ == '__main__':
    try:
        book_checks = excel_to_book(f1_in_checks)
        # book_tasks = excel_to_book(f1_in_tasks)
        # book_output = excel_to_book(f2_out)
    except Exception as e:
        raise e

    book_to_kwargs_output(book_output)
    # kwargs = book_to_kwargs(book_checks, book_tasks,book_output)
    # kwargs = book_to_kwargs_output(book_output)