import yaml
import argparse
from termcolor import colored
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
parser.add_argument("-V", "--version", help="show program version", action="store_true")
# parser.add_argument()

args = parser.parse_args()
if args.version:
    print("current version {}".format(VERSION))

# Read YAML file
try:
    with open("config.yaml", 'r') as stream:
        config_loaded = yaml.safe_load(stream)
except e as Exception:
    raise (e)

import ipdb
ipdb.set_trace()