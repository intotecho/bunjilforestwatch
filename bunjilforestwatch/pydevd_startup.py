# From https://docs.google.com/document/d/1CCSaRiIWCLgbD3OwmuKsRoHHDfBffbROWyVWWL0ZXN4/edit#
import json 
import sys 

options = {'host': 'localhost', 'port': 8001} 

if config.python_config.startup_args: 
    options.update(json.loads(config.python_config.startup_args)) 

if ':' not in config.version_id:
      # The default server version_id does not contain ':'
      sys.path.append(<path to the pydevd directory>)
      import pydevd 
      pydevd.settrace(options['host'], port=options['port'], 
                  stdoutToServer=False, stderrToServer=True)
