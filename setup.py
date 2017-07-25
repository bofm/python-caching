from setuptools import setup
from setuptools.command.test import test as TestCommand


with open('requirements.txt') as f:
    reqs = [line for line in f if line and not line.startswith('#')]


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
    version='0.1',
    packages=['caching'],
    author='bofm',
    author_email='bofm@github.com',
    description='Python utils and decorators for cаching',
    install_requires=reqs,
    tests_require=['pytest'],
    cmdclass={'test': PyTest},
)

