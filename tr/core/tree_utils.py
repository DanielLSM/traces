import treelib

from collections import OrderedDict


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
                 *args,
                 **kwargs):
        day_str = day.strftime("%m/%d/%Y")

        if tag is None:
            tag = '{}_{}'.format(day_str, action_maintenance)

        super().__init__(tag=tag, *args, **kwargs)
        self.calendar = calendar
        self.day = day
        self.fleet_state = fleet_state
        self.assignment = assignment  # state of the world
        self.action_maintenance = action_maintenance
        self.count = 0
        self.on_c_maintenance = on_c_maintenance
        self.c_maintenance_counter = c_maintenance_counter


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


# def build_non_operating_fleet_state(fleet, type_check='C'):
#     fleet_state = OrderedDict()
#     for key in fleet.aircraft_info.keys():
#         fleet_state[key] = {}
#         fleet_state[key]['DY-C'.format(type_check)] = fleet.aircraft_info[key][
#             '{}_INITIAL'.format(type_check)]['DY-{}'.format(type_check)]
#         fleet_state[key]['FH-{}'.format(
#             type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
#                 type_check)]['FH-{}'.format(type_check)]
#         fleet_state[key]['FC-{}'.format(
#             type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
#                 type_check)]['FH-{}'.format(type_check)]
#         fleet_state[key]['DY-{}-MAX'.format(
#             type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
#                 type_check)]['{}-CI-DY'.format(type_check)]
#         fleet_state[key]['FH-{}-MAX'.format(
#             type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
#                 type_check)]['{}-CI-FH'.format(type_check)]
#         fleet_state[key]['FC-{}-MAX'.format(
#             type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
#                 type_check)]['{}-CI-FH'.format(type_check)]
#         fleet_state[key]['{}-SN'.format(
#             type_check)] = fleet.aircraft_info[key]['{}_INITIAL'.format(
#                 type_check)]['{}-SN'.format(type_check)]
#         fleet_state[key]['OPERATING'] = True
#     return fleet_state