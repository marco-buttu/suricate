from __future__ import with_statement
import os
import sys
import logging
import yaml

from suricate.paths import (
    suricate_dir,
    config_dir,
    config_file,
    log_dir,
)


# --- DEFAULT CONFIGURATION PARAMETERS
default_config = { 
    'COMPONENTS': {
        "TestNamespace/Positioner00": {
            'properties': [
                {"name": "position", "timer": 0.1},
                {"name": "current", "timer": 0.1},
                {"name": "seq", "timer": 0.1},
            ],
            'methods': [
                {"name": "getPosition", "timer": 0.1},
                {"name": "getSequence", "timer": 0.1},
            ],
        },
        "TestNamespace/Positioner01": {
            "properties": [
                {"name": "current", "timer": 0.1}
            ],
        } 
    },

    'SCHEDULER': {
        'RESCHEDULE_INTERVAL': 1,  # Seconds
        'RESCHEDULE_ERROR_INTERVAL': 2,  # Seconds
    },

    'HTTP': {
        'port': 5000,  # Web app port
        'baseurl': 'http://127.0.0.1',  # Web app URL
    },
}


# ---- LOGGING CONFIGURATION
formatter = logging.Formatter(
    '%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)
aps_logfile = os.path.join(log_dir, 'apscheduler.log')
aps_handler = logging.FileHandler(aps_logfile)
aps_handler.setFormatter(formatter)
logging.getLogger('apscheduler').addHandler(aps_handler)
logging.getLogger('apscheduler').setLevel(logging.WARNING)

sur_logfile = os.path.join(log_dir, 'suricate.log')
sur_file_handler = logging.FileHandler(sur_logfile)
sur_file_handler.setFormatter(formatter)
sur_stream_handler = logging.StreamHandler(sys.stdout)
sur_stream_handler.setFormatter(formatter)
logging.getLogger('suricate').addHandler(sur_file_handler)
logging.getLogger('suricate').addHandler(sur_stream_handler)
logging.getLogger('suricate').setLevel(logging.INFO)


try:
    with open(config_file) as stream:
        config = yaml.safe_load(stream)
        if not config:
            config = default_config
except Exception:
        config = default_config
