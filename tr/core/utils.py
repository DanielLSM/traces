import pandas as pd
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import OrderedDict, defaultdict

# from tr.core.schedule_classes import Calendar, Check


def advance_date(date, *args, **kwargs):
    return date + relativedelta(**kwargs)


def advance_date_now(*args, **kwargs):
    return datetime.now() + relativedelta(**kwargs)


def dates_between(date_start, date_end, *args, **kwargs):
    assert date_end > date_start, "end date before start_date"
    delta = date_end - date_start
    return delta.days


def dict_to_list(pandas_dict):
    pandas_list = []
    for value in pandas_dict.values():
        pandas_list.append(value)
    assert len(pandas_list) == len(list(pandas_dict.keys()))
    return pandas_list


def diff_time_list(sheet, type='days'):
    # in the future we would like to...... use types different than days
    sheet_keys = list(sheet.keys())
    assert 'BEGIN' in sheet_keys and 'END' in sheet_keys, "undefined"
    time_list = []
    for _ in sheet['BEGIN'].keys():
        delta = sheet['END'][_] - sheet['BEGIN'][_]
        time_list.extend([
            sheet['BEGIN'][_] + timedelta(days=i)
            for i in range(delta.days + 1)
        ])
    return time_list


def get_slots(sheet):
    assert 'SLOTS' in sheet.keys(), "slots are not in sheet keys"
    if 'DATE' in sheet.keys():
        slots = {
            sheet['DATE'][_]: sheet['SLOTS'][_]
            for _ in range(list(sheet['SLOTS'].keys())[-1] + 1)
        }
        assert len(list(slots.keys())) == len(list(sheet['SLOTS'].keys()))
    elif 'BEGIN' in sheet.keys():
        slots = {}
        for _ in sheet['BEGIN'].keys():
            delta = sheet['END'][_] - sheet['BEGIN'][_]
            slots_per_entry = {
                sheet['BEGIN'][_] + timedelta(days=i): sheet['SLOTS'][_]
                for i in range(delta.days + 1)
            }
            slots.update(slots_per_entry)
    return slots


if __name__ == '__main__':
    # book = excel_to_book(f1_in)
    # book_to_calendar(book)
    # aircraft_info = book_to_aircraft_info(book)
    # for _ in aircraft_info:
    #     print(_)

    date = advance_date_now(days=-2)

    # print(advance_date_now(days=1, weeks=1, months=1, years=1))
