#!/usr/bin/env python
"""
pgxnclient -- setup script
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client


import os
import sys
from setuptools import setup, find_packages

# Grab the version without importing the module
# or we will get import errors on install if prerequisites are still missing
fn = os.path.join(os.path.dirname(__file__), 'pgxnclient', '__init__.py')
f = open(fn)
try:
    for line in f:
        if line.startswith('__version__ ='):
            version = line.split("'")[1]
            break
    else:
        raise ValueError('cannot find __version__ in the pgxnclient module')
finally:
    f.close()

# External dependencies, depending on the Python version
requires = ['six']
tests_require = ['mock']

if sys.version_info < (2, 7):
    raise ValueError("PGXN client requires at least Python 2.7")
if (3,) < sys.version_info < (3, 4):
    raise ValueError("PGXN client requires at least Python 3.4")


classifiers = """
Development Status :: 5 - Production/Stable
Environment :: Console
Intended Audience :: Developers
Intended Audience :: System Administrators
License :: OSI Approved :: BSD License
Operating System :: POSIX
Programming Language :: Python :: 2
Programming Language :: Python :: 3
Topic :: Database
"""

setup(
    name = 'pgxnclient',
    description = 'A command line tool to interact with the PostgreSQL Extension Network.',
    author = 'Daniele Varrazzo',
    author_email = 'daniele.varrazzo@gmail.com',
    url = 'https://github.com/dvarrazzo/pgxnclient',
    license = 'BSD',
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    packages = find_packages(),
    package_data = {'pgxnclient': ['libexec/*']},
    entry_points = {'console_scripts': [
        'pgxn = pgxnclient.cli:command_dispatch',
        'pgxnclient = pgxnclient.cli:script', ]},
    test_suite = 'pgxnclient.tests',
    classifiers = [x for x in classifiers.split('\n') if x],
    zip_safe = False,   # because we dynamically look for commands
    install_requires = requires,
    tests_require = tests_require,
    version = version,
)

