#!/usr/bin/env python3

from toml import loads

from flowbber.pipeline import Pipeline
from flowbber.scheduler import Scheduler
from flowbber.logging import setup_logging


CONFIG = """
[cpud]
verbosity = 3

[sampling]
# Take a sample each 10 seconds
frequency = 10

[influxdb]
uri = "influxdb://localhost:8086/"
database = "cpud"

[mongodb]
uri = "mongodb://localhost:27017/"
database = "cpud"
collection = "cpuddata"
"""


def build_definition(config):
    """
    Build a pipeline definition based on given configuration.
    """
    definition = {
        'sources': [
            {'type': 'cpu', 'id': 'cpu'},
        ],
        'sinks': [],
        'aggregators': [],
    }

    if config['influxdb']:
        definition['sinks'].append({
            'type': 'influxdb',
            'id': 'influxdb',
            'config': {
                'uri': config['influxdb']['uri'],
                'database': config['influxdb']['database'],
                'key': None,
            }
        })

    if config['mongodb']:
        definition['sinks'].append({
            'type': 'mongodb',
            'id': 'mongodb',
            'config': {
                'uri': config['mongodb']['uri'],
                'database': config['mongodb']['database'],
                'collection': config['mongodb']['collection'],
                'key': None,
            }
        })

    if not definition['sinks']:
        raise RuntimeError('No sinks configured')

    return definition


def main():

    # Read configuration
    config = loads(CONFIG)

    # Setup multiprocess logging
    setup_logging(config['cpud']['verbosity'])

    # Build pipeline definition
    definition = build_definition(config)

    # Build pipeline
    pipeline = Pipeline(
        definition,
        'cpud',
        app='cpud',
        save_journal=False,
    )

    # Build and run scheduler
    scheduler = Scheduler(
        pipeline,
        config['sampling']['frequency'],
        stop_on_failure=True
    )

    scheduler.run()


if __name__ == '__main__':
    main()
