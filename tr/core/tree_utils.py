import treelib
import pandas as pd

from collections import OrderedDict

from tr.core.parsers import excel_to_book


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
                 on_maintenance_merged=[],
                 fleet_phasing_out={},
                 phased_out={}):
        day_str = day.strftime("%m/%d/%Y")

        if tag is None:
            tag = '{}_{}'.format(day_str, action_maintenance)

        super().__init__(tag=tag)
        self.calendar = calendar
        self.day = day
        self.fleet_state = fleet_state
        self.fleet_phasing_out = fleet_phasing_out
        self.assignment = assignment  # state of the world
        self.action_maintenance = action_maintenance
        self.count = 0
        self.on_c_maintenance = on_c_maintenance
        self.c_maintenance_counter = c_maintenance_counter
        self.on_c_maintenance_tats = on_c_maintenance_tats
        self.merged_with_c = merged_with_c
        self.on_maintenance_merged = on_maintenance_merged
        self.phased_out = phased_out


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
                        type_check)] - fleet_state[aircraft]['DY-{}'.format(type_check)]
                fleet_state[aircraft]['FH-{}-WASTE'.format(
                    type_check)] = fleet_state[aircraft]['FH-{}-MAX'.format(
                        type_check)] - fleet_state[aircraft]['FH-{}'.format(type_check)]
                fleet_state[aircraft]['FC-{}-WASTE'.format(
                    type_check)] = fleet_state[aircraft]['FC-{}-MAX'.format(
                        type_check)] - fleet_state[aircraft]['FC-{}'.format(type_check)]
                code = fleet_state[aircraft]['{}-SN'.format(type_check)]
                fleet_state[aircraft]['{}-SN'.format(type_check)] = code_generator[type_check](code)
                fleet_state[aircraft]['OPERATING'] = False

            fleet_state[aircraft]['DY-{}'.format(type_check)] = 0
            fleet_state[aircraft]['FH-{}'.format(type_check)] = 0
            fleet_state[aircraft]['FC-{}'.format(type_check)] = 0
        else:
            if aircraft in on_c_maintenance:
                fleet_state[aircraft]['DY-{}'.format(type_check)] = fleet_state[aircraft][
                    'DY-{}'.format(type_check)]
                fleet_state[aircraft]['FH-{}'.format(type_check)] = fleet_state[aircraft][
                    'FH-{}'.format(type_check)]
                fleet_state[aircraft]['FC-{}'.format(type_check)] = fleet_state[aircraft][
                    'FC-{}'.format(type_check)]
            else:
                fleet_state[aircraft]['DY-{}'.format(type_check)] += 1
                month = (date.month_name()[0:3]).upper()
                fleet_state[aircraft]['FH-{}'.format(
                    type_check)] += utilization_ratio[aircraft]['DFH'][month]
                fleet_state[aircraft]['FC-{}'.format(
                    type_check)] += utilization_ratio[aircraft]['DFC'][month]
                fleet_state[aircraft]['OPERATING'] = True

        fleet_state[aircraft]['DY-{}-RATIO'.format(type_check)] = fleet_state[aircraft][
            'DY-{}'.format(type_check)] / fleet_state[aircraft]['DY-{}-MAX'.format(type_check)]
        fleet_state[aircraft]['FH-{}-RATIO'.format(type_check)] = fleet_state[aircraft][
            'FH-{}'.format(type_check)] / fleet_state[aircraft]['FH-{}-MAX'.format(type_check)]
        fleet_state[aircraft]['FC-{}-RATIO'.format(type_check)] = fleet_state[aircraft][
            'FC-{}'.format(type_check)] / fleet_state[aircraft]['FC-{}-MAX'.format(type_check)]
        fleet_state[aircraft]['TOTAL-RATIO'] = max([
            fleet_state[aircraft]['DY-{}-RATIO'.format(type_check)],
            fleet_state[aircraft]['FH-{}-RATIO'.format(type_check)],
            fleet_state[aircraft]['FC-{}-RATIO'.format(type_check)]
        ])
    return fleet_state


def fleet_operate_C(**kwargs):

    fleet_state = kwargs['fleet_state']
    date = kwargs['date']
    on_maintenance = kwargs['on_maintenance']
    type_check = kwargs['type_check']
    utilization_ratio = kwargs['utilization_ratio']
    code_generator = kwargs['code_generator']
    type_D_check = kwargs['type_D_check']

    # if 'Aircraft-48' in on_maintenance:
    #     import ipdb
    #     ipdb.set_trace()

    for aircraft in fleet_state.keys():
        if aircraft in on_maintenance:
            # dont worry with this if, an aircraft will never be selected
            # on A-check again, but in C-check will
            if fleet_state[aircraft]['OPERATING']:
                fleet_state[aircraft]['DY-{}-WASTE'.format(
                    type_check)] = fleet_state[aircraft]['DY-{}-MAX'.format(
                        type_check)] - fleet_state[aircraft]['DY-{}'.format(type_check)]
                fleet_state[aircraft]['FH-{}-WASTE'.format(
                    type_check)] = fleet_state[aircraft]['FH-{}-MAX'.format(
                        type_check)] - fleet_state[aircraft]['FH-{}'.format(type_check)]
                fleet_state[aircraft]['FC-{}-WASTE'.format(
                    type_check)] = fleet_state[aircraft]['FC-{}-MAX'.format(
                        type_check)] - fleet_state[aircraft]['FC-{}'.format(type_check)]
                # code = fleet_state[aircraft]['{}-SN'.format(type_check)]
                d_check_code = fleet_state[aircraft]['D-CYCLE']
                d_check_limit = fleet_state[aircraft]['D-CYCLE-MAX']
                fleet_state[aircraft]['D-CYCLE'] = generate_D_check_code(
                    d_check_limit, d_check_code)

                code = fleet_state[aircraft]['{}-SN'.format(type_check)]
                fleet_state[aircraft]['{}-SN'.format(type_check)] = code_generator[type_check](code)
                fleet_state[aircraft]['OPERATING'] = False
            fleet_state[aircraft]['DY-{}'.format(type_check)] = 0
            fleet_state[aircraft]['FH-{}'.format(type_check)] = 0
            fleet_state[aircraft]['FC-{}'.format(type_check)] = 0
            if type_D_check:
                fleet_state[aircraft]['DY-D'.format(type_check)] = 0
                fleet_state[aircraft]['D-CYCLE'] = 1
        else:
            fleet_state[aircraft]['DY-{}'.format(type_check)] += 1
            fleet_state[aircraft]['DY-D'.format(type_check)] += 1
            month = (date.month_name()[0:3]).upper()
            fleet_state[aircraft]['FH-{}'.format(
                type_check)] += utilization_ratio[aircraft]['DFH'][month]
            fleet_state[aircraft]['FC-{}'.format(
                type_check)] += utilization_ratio[aircraft]['DFC'][month]
            fleet_state[aircraft]['OPERATING'] = True

        fleet_state[aircraft]['DY-{}-RATIO'.format(type_check)] = fleet_state[aircraft][
            'DY-{}'.format(type_check)] / fleet_state[aircraft]['DY-{}-MAX'.format(type_check)]
        fleet_state[aircraft]['FH-{}-RATIO'.format(type_check)] = fleet_state[aircraft][
            'FH-{}'.format(type_check)] / fleet_state[aircraft]['FH-{}-MAX'.format(type_check)]
        fleet_state[aircraft]['FC-{}-RATIO'.format(type_check)] = fleet_state[aircraft][
            'FC-{}'.format(type_check)] / fleet_state[aircraft]['FC-{}-MAX'.format(type_check)]
        fleet_state[aircraft][
            'DY-D-RATIO'] = fleet_state[aircraft]['DY-D'] / fleet_state[aircraft]['DY-D-MAX']
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
        fleet_state[key]['DY-{}'.format(type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
            type_check)]['DY-{}'.format(type_check)]
        fleet_state[key]['FH-{}'.format(type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
            type_check)]['FH-{}'.format(type_check)]
        fleet_state[key]['FC-{}'.format(type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
            type_check)]['FH-{}'.format(type_check)]
        fleet_state[key]['DY-{}-MAX'.format(type_check)] = fleet.aircraft_info[key][
            '{}_INITIAL'.format(type_check)]['{}-CI-DY'.format(type_check)]
        fleet_state[key]['FH-{}-MAX'.format(type_check)] = fleet.aircraft_info[key][
            '{}_INITIAL'.format(type_check)]['{}-CI-FH'.format(type_check)]
        fleet_state[key]['FC-{}-MAX'.format(type_check)] = fleet.aircraft_info[key][
            '{}_INITIAL'.format(type_check)]['{}-CI-FH'.format(type_check)]
        fleet_state[key]['A-SN'] = fleet.aircraft_info[key]['A_INITIAL']['A-SN']
        fleet_state[key]['C-SN'] = fleet.aircraft_info[key]['C_INITIAL']['C-SN']
        # fleet_state[key]['{}-SN'.format(
        #     type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
        #         type_check)]['{}-SN'.format(type_check)]
        fleet_state[key]['DY-{}-RATIO'.format(type_check)] = fleet_state[key]['DY-{}'.format(
            type_check)] / fleet_state[key]['DY-{}-MAX'.format(type_check)]
        fleet_state[key]['FH-{}-RATIO'.format(type_check)] = fleet_state[key]['FH-{}'.format(
            type_check)] / fleet_state[key]['FH-{}-MAX'.format(type_check)]
        fleet_state[key]['FC-{}-RATIO'.format(type_check)] = fleet_state[key]['FC-{}'.format(
            type_check)] / fleet_state[key]['FC-{}-MAX'.format(type_check)]

        if type_check == 'C':
            fleet_state[key]['D-CYCLE'] = fleet.aircraft_info[key]['D_INITIAL']['D-CYCLE']
            fleet_state[key]['DY-D'] = fleet.aircraft_info[key]['D_INITIAL']['DY-D']
            fleet_state[key]['DY-D-MAX'] = fleet.aircraft_info[key]['D_INITIAL']['D-CI-DY']
            fleet_state[key]['D-CYCLE-MAX'] = fleet.aircraft_info[key]['D_INITIAL']['D-MAX']
            fleet_state[key]['DY-D-RATIO'] = fleet_state[key]['DY-D'] / fleet_state[key]['DY-D-MAX']
            fleet_state[key]['TOTAL-RATIO'] = max([
                fleet_state[key]['DY-{}-RATIO'.format(type_check)],
                fleet_state[key]['FH-{}-RATIO'.format(type_check)],
                fleet_state[key]['FC-{}-RATIO'.format(type_check)], fleet_state[key]['DY-D-RATIO']
            ])

        else:
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
    return OrderedDict(sorted(fleet_state.items(), key=lambda x: x[1]['TOTAL-RATIO'], reverse=True))


def generate_D_check_code(limit, last_code):
    code = (int(last_code) + 1) % (limit + 1)
    if code == 0:
        code = 1
    return code


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
