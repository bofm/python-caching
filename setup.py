import re
import os

from setuptools import setup
from setuptools.command.test import test as TestCommand


def get_version(filepath):
    with open(filepath) as f:
        match = re.search("__version__ = '(.*?)'", f.read(8192))
        if not match:
            raise RuntimeError('Could not find version.')
        version = match.group(1)
        return version


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', "Arguments to pass into py.test")]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest

        errno = pytest.main(self.pytest_args)
        raise SystemExit(errno)


setup(
    name='caching',
    version=get_version(os.path.join('caching', '__init__.py')),
    packages=['caching'],
    author='bofm',
    author_email='bofm@github.com',
    description='Python utils and decorators for cаching',
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
)
