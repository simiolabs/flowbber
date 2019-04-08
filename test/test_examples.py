from os import environ
from pathlib import Path
from subprocess import run
from collections import namedtuple

from pytest import mark, skip

from flowbber.main import main
from flowbber.logging import get_logger, setup_logging


Arguments = namedtuple('Arguments', ['pipeline', 'dry_run'])


log = get_logger(__name__)
examples = Path(__file__).parent.parent / 'examples'


def setup_module(module):
    setup_logging(verbosity=2)


@mark.parametrize(['name', 'pipelinedef'], [
    ['advanced', 'pipeline.toml'],
    ['advanced', 'pipeline.json'],
    ['archive', 'compress.toml'],
    ['archive', 'extract.toml'],
    ['basic', 'pipeline.toml'],
    ['config', 'pipeline.toml'],
    ['cpu', 'pipeline.toml'],
    ['github', 'pipeline.toml'],
    ['lcov', 'pipeline.toml'],
    ['local', 'pipeline.toml'],
    ['sloc', 'pipeline.toml'],
    ['test', 'pipeline.toml'],
    ['valgrind', 'pipeline.toml'],
])
def test_pipelines(name, pipelinedef):
    # Exceptions ...
    if name == 'github':
        if 'GITHUB_TOKEN' not in environ:
            skip('Missing GITHUB_TOKEN environment variable')

    elif name == 'lcov':
        # Create coverage files
        run(['make', '-C', str(examples / name)], check=True)

    # Run pipeline
    args = Arguments(
        pipeline=examples / name / pipelinedef,
        dry_run=False,
    )
    result = main(args)
    assert result == 0


@mark.parametrize(['script'], [
    ['cpud/cpud.py'],
    # Aug 22 2018:
    #   The package pytestspeed is broken.
    #   https://github.com/fopina/pyspeedtest/issues/15
    # ['speedd/speedd.py'],
])
def test_daemons(script):
    run(str(examples / script), check=True)
