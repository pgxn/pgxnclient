#!/usr/bin/env python
"""
pgxnclient -- setup script
"""

# Copyright (C) 2011 Daniele Varrazzo

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
requires = []

if sys.version_info < (2, 5):
    requires.append('simplejson<=2.0.9')
elif sys.version_info < (2, 6):
    requires.append('simplejson')

# Note that testing also requires unittest2 and mock:
# 'make env' can install them locally.


setup(
    name = 'pgxnclient',
    description = 'A command line tool to interact with the PostgreSQL Extension Network.',
    author = 'Daniele Varrazzo',
    author_email = 'daniele.varrazzo@gmail.com',
    url = 'http://pgxnclient.projects.postgresql.org/',
    license = 'BSD',
    packages = find_packages(exclude=["tests"]),
    entry_points = {'console_scripts': ['pgxn = pgxnclient.cli:script']},
    zip_safe = False,   # because we dynamically look for commands
    install_requires = requires,
    version = version,
    use_2to3 = True,
)

# Note: I've not been able to include data files using 'package_data':
# using MANIFEST.in for the purpose.

