# from calc import calc as real_calc
import sys
import zerorpc
from tr.core.edf import *

# from tr.core.parsers import excel_to_book, book_to_kwargs


class SchedulerRest(SchedulerEDF):
    def __init__(self, *args, **kwargs):
        SchedulerEDF.__init__(self, **kwargs)

    def server_plan_opportunities(self):
        self.plan_maintenance_opportunities()

    def server_plan_tasks(self):
        self.pre_process_tasks()
        self.plan_tasks_fleet()
        print("INFO: Task plan complete")

    def server_save_checks_xlsx(self):
        self.save_checks_to_xlsx()

    def server_save_tasks_xlsx(self):
        self.save_tasks_to_xlsx()

    def server_save_checks(self):
        self.save_checks_pickle()

    def server_load_checks(self):
        self.load_checks_pickle()

    def server_save_tasks(self):
        self.save_tasks_pickle()

    def server_load_tasks(self):
        self.load_checks_tasks()


# class CalcApi(object):
#     def calc(self, text):
#         """based on the input text, return the int result"""
#         try:
#             return real_calc(text)
#         except Exception as e:
#             return 0.0

#     def echo(self, text):
#         """echo any text"""
#         return text


def parse_port():
    return "4242"


def main():
    # addr = 'tcp://127.0.0.1:' + parse_port()
    # s = zerorpc.Server(CalcApi())
    # s.bind(addr)
    # print('start running on {}'.format(addr))
    # s.run()

    import time
    from resources import f1_in_checks, f1_in_tasks
    t = time.time()
    try:
        book_checks = excel_to_book(f1_in_checks)
        book_tasks = excel_to_book(f1_in_tasks)
    except Exception as e:
        raise e

    kwargs = book_to_kwargs(book_checks, book_tasks)
    addr = 'tcp://127.0.0.1:' + parse_port()
    s = zerorpc.Server(SchedulerRest(**kwargs))
    s.bind(addr)
    print("###################################")
    print('INFO: Server started running on {}'.format(addr))
    s.run()

    # scheduler = SchedulerEDF(**kwargs)
    print("INFO: total elapsed time {} seconds".format(time.time() - t))


if __name__ == '__main__':
    main()