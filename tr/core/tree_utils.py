import treelib
import pandas as pd

from collections import OrderedDict

from tr.core.parsers import excel_to_book
from tr.core.resources import f2_out


class NodeScheduleDays(treelib.Node):
    def __init__(self,
                 calendar,
                 day,
                 fleet_state,
                 action_maintenance,
                 assignment=[],
                 tag=None,
                 identifier=None,
                 on_c_maintenance=[],
                 c_maintenance_counter=0,
                 on_c_maintenance_tats={},
                 merged_with_c=[],
                 on_maintenance_merged=[]):
        day_str = day.strftime("%m/%d/%Y")

        if tag is None:
            tag = '{}_{}'.format(day_str, action_maintenance)

        super().__init__(tag=tag)
        self.calendar = calendar
        self.day = day
        self.fleet_state = fleet_state
        self.assignment = assignment  # state of the world
        self.action_maintenance = action_maintenance
        self.count = 0
        self.on_c_maintenance = on_c_maintenance
        self.c_maintenance_counter = c_maintenance_counter
        self.on_c_maintenance_tats = on_c_maintenance_tats
        self.merged_with_c = merged_with_c
        self.on_maintenance_merged = on_maintenance_merged


def fleet_operate_A(**kwargs):
    #  kwargs = {
    #         'fleet_state': fleet_state,
    #         'date': date,
    #         'on_maintenance': on_maintenance,
    #         'type_check': type_check,
    #         'on_c_maintenance': on_c_maintenance,
    #         'utilization_ratio':self.utilization_ratio,
    #         'code_generator': self.code_generator
    #     }

    fleet_state = kwargs['fleet_state']
    date = kwargs['date']
    on_maintenance = kwargs['on_maintenance']
    type_check = kwargs['type_check']
    on_c_maintenance = kwargs['on_c_maintenance']
    utilization_ratio = kwargs['utilization_ratio']
    code_generator = kwargs['code_generator']

    for aircraft in fleet_state.keys():

        if aircraft in on_maintenance:
            # dont worry with this if, an aircraft will never be selected
            # on A-check again, but in C-check will
            if fleet_state[aircraft]['OPERATING']:
                fleet_state[aircraft]['DY-{}-WASTE'.format(
                    type_check)] = fleet_state[aircraft]['DY-{}-MAX'.format(
                        type_check)] - fleet_state[aircraft]['DY-{}'.format(
                            type_check)]
                fleet_state[aircraft]['FH-{}-WASTE'.format(
                    type_check)] = fleet_state[aircraft]['FH-{}-MAX'.format(
                        type_check)] - fleet_state[aircraft]['FH-{}'.format(
                            type_check)]
                fleet_state[aircraft]['FC-{}-WASTE'.format(
                    type_check)] = fleet_state[aircraft]['FC-{}-MAX'.format(
                        type_check)] - fleet_state[aircraft]['FC-{}'.format(
                            type_check)]
                code = fleet_state[aircraft]['{}-SN'.format(type_check)]
                fleet_state[aircraft]['{}-SN'.format(
                    type_check)] = code_generator[type_check](code)
                fleet_state[aircraft]['OPERATING'] = False
        
            fleet_state[aircraft]['DY-{}'.format(type_check)] = 0
            fleet_state[aircraft]['FH-{}'.format(type_check)] = 0
            fleet_state[aircraft]['FC-{}'.format(type_check)] = 0
        else:
            if aircraft in on_c_maintenance:
                fleet_state[aircraft]['DY-{}'.format(type_check)] = fleet_state[aircraft]['DY-{}'.format(type_check)]
                fleet_state[aircraft]['FH-{}'.format(type_check)] = fleet_state[aircraft]['FH-{}'.format(type_check)]
                fleet_state[aircraft]['FC-{}'.format(type_check)] = fleet_state[aircraft]['FC-{}'.format(type_check)]
            else:
                fleet_state[aircraft]['DY-{}'.format(type_check)] += 1
                month = (date.month_name()[0:3]).upper()
                fleet_state[aircraft]['FH-{}'.format(
                    type_check)] += utilization_ratio[aircraft]['DFH'][month]
                fleet_state[aircraft]['FC-{}'.format(
                    type_check)] += utilization_ratio[aircraft]['DFC'][month]
                fleet_state[aircraft]['OPERATING'] = True

        fleet_state[aircraft]['DY-{}-RATIO'.format(
            type_check)] = fleet_state[aircraft]['DY-{}'.format(
                type_check)] / fleet_state[aircraft]['DY-{}-MAX'.format(
                    type_check)]
        fleet_state[aircraft]['FH-{}-RATIO'.format(
            type_check)] = fleet_state[aircraft]['FH-{}'.format(
                type_check)] / fleet_state[aircraft]['FH-{}-MAX'.format(
                    type_check)]
        fleet_state[aircraft]['FC-{}-RATIO'.format(
            type_check)] = fleet_state[aircraft]['FC-{}'.format(
                type_check)] / fleet_state[aircraft]['FC-{}-MAX'.format(
                    type_check)]
        fleet_state[aircraft]['TOTAL-RATIO'] = max([
            fleet_state[aircraft]['DY-{}-RATIO'.format(type_check)],
            fleet_state[aircraft]['FH-{}-RATIO'.format(type_check)],
            fleet_state[aircraft]['FC-{}-RATIO'.format(type_check)]
        ])
    return fleet_state


def fleet_operate_C(**kwargs):
    #  kwargs = {
    #         'fleet_state': fleet_state,
    #         'date': date,
    #         'on_maintenance': on_maintenance,
    #         'type_check': type_check
    #         'utilization_ratio':self.utilization_ratio,
    #         'code_generator': self.code_generator
    #     }

    fleet_state = kwargs['fleet_state']
    date = kwargs['date']
    on_maintenance = kwargs['on_maintenance']
    type_check = kwargs['type_check']
    utilization_ratio = kwargs['utilization_ratio']
    code_generator = kwargs['code_generator']

    # import ipdb
    # ipdb.set_trace()
    for aircraft in fleet_state.keys():
        if aircraft in on_maintenance:
            # dont worry with this if, an aircraft will never be selected
            # on A-check again, but in C-check will
            if fleet_state[aircraft]['OPERATING']:
                fleet_state[aircraft]['DY-{}-WASTE'.format(
                    type_check)] = fleet_state[aircraft]['DY-{}-MAX'.format(
                        type_check)] - fleet_state[aircraft]['DY-{}'.format(
                            type_check)]
                fleet_state[aircraft]['FH-{}-WASTE'.format(
                    type_check)] = fleet_state[aircraft]['FH-{}-MAX'.format(
                        type_check)] - fleet_state[aircraft]['FH-{}'.format(
                            type_check)]
                fleet_state[aircraft]['FC-{}-WASTE'.format(
                    type_check)] = fleet_state[aircraft]['FC-{}-MAX'.format(
                        type_check)] - fleet_state[aircraft]['FC-{}'.format(
                            type_check)]
                code = fleet_state[aircraft]['{}-SN'.format(type_check)]
                fleet_state[aircraft]['{}-SN'.format(
                    type_check)] = code_generator[type_check](code)
                # fleet_state[aircraft]['DY-{}'.format(type_check)] = fleet_state[aircraft]['DY-{}'.format(type_check)]
                # fleet_state[aircraft]['FH-{}'.format(type_check)] = fleet_state[aircraft]['FH-{}'.format(type_check)]
                # fleet_state[aircraft]['FC-{}'.format(type_check)] = fleet_state[aircraft]['FC-{}'.format(type_check)]
                fleet_state[aircraft]['OPERATING'] = False
            fleet_state[aircraft]['DY-{}'.format(type_check)] = 0
            fleet_state[aircraft]['FH-{}'.format(type_check)] = 0
            fleet_state[aircraft]['FC-{}'.format(type_check)] = 0
        else:
            fleet_state[aircraft]['DY-{}'.format(type_check)] += 1
            month = (date.month_name()[0:3]).upper()
            fleet_state[aircraft]['FH-{}'.format(
                type_check)] += utilization_ratio[aircraft]['DFH'][month]
            fleet_state[aircraft]['FC-{}'.format(
                type_check)] += utilization_ratio[aircraft]['DFC'][month]
            fleet_state[aircraft]['OPERATING'] = True

        fleet_state[aircraft]['DY-{}-RATIO'.format(
            type_check)] = fleet_state[aircraft]['DY-{}'.format(
                type_check)] / fleet_state[aircraft]['DY-{}-MAX'.format(
                    type_check)]
        fleet_state[aircraft]['FH-{}-RATIO'.format(
            type_check)] = fleet_state[aircraft]['FH-{}'.format(
                type_check)] / fleet_state[aircraft]['FH-{}-MAX'.format(
                    type_check)]
        fleet_state[aircraft]['FC-{}-RATIO'.format(
            type_check)] = fleet_state[aircraft]['FC-{}'.format(
                type_check)] / fleet_state[aircraft]['FC-{}-MAX'.format(
                    type_check)]
        fleet_state[aircraft]['TOTAL-RATIO'] = max([
            fleet_state[aircraft]['DY-{}-RATIO'.format(type_check)],
            fleet_state[aircraft]['FH-{}-RATIO'.format(type_check)],
            fleet_state[aircraft]['FC-{}-RATIO'.format(type_check)]
        ])
    return fleet_state


def build_fleet_state(fleet, type_check='A'):
    fleet_state = OrderedDict()
    for key in fleet.aircraft_info.keys():
        fleet_state[key] = {}
        fleet_state[key]['DY-{}'.format(
            type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
                type_check)]['DY-{}'.format(type_check)]
        fleet_state[key]['FH-{}'.format(
            type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
                type_check)]['FH-{}'.format(type_check)]
        fleet_state[key]['FC-{}'.format(
            type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
                type_check)]['FH-{}'.format(type_check)]
        fleet_state[key]['DY-{}-MAX'.format(
            type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
                type_check)]['{}-CI-DY'.format(type_check)]
        fleet_state[key]['FH-{}-MAX'.format(
            type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
                type_check)]['{}-CI-FH'.format(type_check)]
        fleet_state[key]['FC-{}-MAX'.format(
            type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
                type_check)]['{}-CI-FH'.format(type_check)]
        fleet_state[key]['A-SN'] = fleet.aircraft_info[key]['A_INITIAL']['A-SN']
        fleet_state[key]['C-SN'] = fleet.aircraft_info[key]['C_INITIAL']['C-SN']
        fleet_state[key]['{}-SN'.format(
            type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
                type_check)]['{}-SN'.format(type_check)]
        fleet_state[key]['DY-{}-RATIO'.format(
            type_check)] = fleet_state[key]['DY-{}'.format(
                type_check)] / fleet_state[key]['DY-{}-MAX'.format(type_check)]
        fleet_state[key]['FH-{}-RATIO'.format(
            type_check)] = fleet_state[key]['FH-{}'.format(
                type_check)] / fleet_state[key]['FH-{}-MAX'.format(type_check)]
        fleet_state[key]['FC-{}-RATIO'.format(
            type_check)] = fleet_state[key]['FC-{}'.format(
                type_check)] / fleet_state[key]['FC-{}-MAX'.format(type_check)]
        fleet_state[key]['TOTAL-RATIO'] = max([
            fleet_state[key]['DY-{}-RATIO'.format(type_check)],
            fleet_state[key]['FH-{}-RATIO'.format(type_check)],
            fleet_state[key]['FC-{}-RATIO'.format(type_check)]
        ])
        # fleet_state[key]['DY-{}-WASTE'.format(
        #     type_check)] = fleet_state[key]['DY-{}-MAX'.format(
        #         type_check)] - fleet_state[key]['DY-{}'.format(type_check)]
        # fleet_state[key]['FH-{}-WASTE'.format(
        #     type_check)] = fleet_state[key]['FH-{}-MAX'.format(
        #         type_check)] - fleet_state[key]['FH-{}'.format(type_check)]
        # fleet_state[key]['FC-{}-WASTE'.format(
        #     type_check)] = fleet_state[key]['FC-{}-MAX'.format(
        #         type_check)] - fleet_state[key]['FC-{}'.format(type_check)]
        fleet_state[key]['OPERATING'] = True
    return fleet_state


def order_fleet_state(fleet_state):
    return OrderedDict(
        sorted(fleet_state.items(),
               key=lambda x: x[1]['TOTAL-RATIO'],
               reverse=True))


def generate_code(limit, last_code):
    last_code_numbers = str(last_code).split('.')

    rotation_check = (int(last_code_numbers[0]) + 1) % (limit + 1)
    if rotation_check == 0:
        rotation_check = 1
    if rotation_check == 1:
        cardinal_check = int(last_code_numbers[1]) + 1
    else:
        cardinal_check = int(last_code_numbers[1])

    code = '{}.{}'.format(rotation_check, cardinal_check)
    return code


def valid_calendar(calendar):
    # import ipdb
    # ipdb.set_trace()

    daterinos_start = []
    calendar_book = excel_to_book(f2_out)
    for _ in calendar_book['C-CHECK LIST']['START']:
        daterinos = pd.to_datetime(_, format='%m/%d/%Y')
        daterinos_start.append(daterinos)
        for key in calendar.calendar[daterinos]['allowed'].keys():
            if key != 'a-type':
                try:
                    assert calendar.calendar[daterinos]['allowed'][key] == True
                except:
                    import ipdb
                    ipdb.set_trace()

    for _ in calendar_book['C-CHECK LIST']['END']:
        daterinos = pd.to_datetime(_, format='%m/%d/%Y')
        for key in calendar.calendar[daterinos]['allowed'].keys():
            if key != 'a-type':
                try:
                    assert calendar.calendar[daterinos]['allowed'][key] == True
                except:
                    import ipdb
                    ipdb.set_trace()
    return daterinos_start

    # import ipdb
    # ipdb.set_trace()
    # assert self.calendar[daterinos]['allowed']['c-type'] == False
    # assert self.calendar[daterinos]['allowed']['c_allowed'] == False
    # assert self.calendar[daterinos]['allowed']['c_peak'] == False
    # assert self.calendar[daterinos]['allowed']['no_weekends'] == False
    # assert self.calendar[daterinos]['resources']['slots']['c-type'] == 1


if __name__ == '__main__':

    book = excel_to_book(f2_out)
    valid_calendar(book)