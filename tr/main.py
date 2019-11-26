import yaml

# Read YAML file
try:
    with open("config.yaml", 'r') as stream:
        config_loaded = yaml.safe_load(stream)
except e as Exception:
    raise (e)

import ipdb
ipdb.set_trace()