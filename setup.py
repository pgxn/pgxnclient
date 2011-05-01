#!/usr/bin/env python
"""
pgxnclient -- setup script
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client


from distutils.core import setup

from pgxnclient import __version__

setup(name='pgxnclient',
    version=__version__,
    description='A command line tool to interact with the PostgreSQL Extension Network.',
    author='Daniele Varrazzo',
    author_email='daniele.varrazzo@gmail.com',
    url='https://github.com/dvarrazzo/pgxn-client/',
    packages=['pgxnclient', 'pgxnclient.utils'],
    scripts=['scripts/pgxn', 'scripts/pgxncli.py'],
    license='BSD',
)

