#!/usr/bin/env python3
"""Run current frontier unittest classes and plain test functions without pytest.

Supports only the tmp_path fixture actually used by the selected modules.
Unknown fixtures fail loudly. Full historical tests retain their original data
dependencies; --start 534 --end 536 selects the new checkout-local checks.
"""
import argparse
import importlib
import inspect
from pathlib import Path
import tempfile
import unittest


def wrap(function):
    params = list(inspect.signature(function).parameters)
    if params not in ([], ['tmp_path']):
        raise RuntimeError(f'Unsupported fixtures for {function.__name__}: {params}')

    def run():
        if not params:
            function()
        else:
            with tempfile.TemporaryDirectory(prefix='gsmg-test-') as directory:
                function(Path(directory))
    return unittest.FunctionTestCase(run, description=f'{function.__module__}.{function.__name__}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', type=int, default=525)
    parser.add_argument('--end', type=int, default=538)
    args = parser.parse_args()
    suite = unittest.TestSuite()
    for path in sorted(Path(__file__).parent.glob('test_phase*.py')):
        phase = path.name[len('test_phase'):len('test_phase')+3]
        if not phase.isdigit() or not args.start <= int(phase) <= args.end:
            continue
        module = importlib.import_module(path.stem)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(module))
        for name, function in inspect.getmembers(module, inspect.isfunction):
            if name.startswith('test_') and function.__module__ == module.__name__:
                suite.addTest(wrap(function))
    if not suite.countTestCases():
        parser.error('no tests selected')
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
