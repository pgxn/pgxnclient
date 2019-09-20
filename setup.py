#!/usr/bin/env python
"""
pgxnclient -- setup script
"""

# Copyright (C) 2011-2019 Daniele Varrazzo

# This file is part of the PGXN client


import os
import sys
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py

here = os.path.dirname(__file__)

# Grab the version without importing the module
# or we will get import errors on install if prerequisites are still missing
with open(os.path.join(here, 'pgxnclient', '__init__.py')) as f:
    for line in f:
        if line.startswith('__version__ ='):
            version = line.split("'")[1]
            break
    else:
        raise ValueError('cannot find __version__ in the pgxnclient module')

# Read the description from the readme
with open(os.path.join(here, 'README.rst')) as f:
    long_description = f.read()

# External dependencies, depending on the Python version
requires = ['six']
setup_requires = ['pytest-runner']
tests_require = ['mock', 'pytest']

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


class CustomBuildPy(build_py):
    def run(self):
        build_py.run(self)
        self.fix_libexec_hashbangs()

    def fix_libexec_hashbangs(self):
        """Replace the hashbangs of the scripts in libexec."""
        for package, src_dir, build_dir, filenames in self.data_files:
            if package != 'pgxnclient':
                continue
            for filename in filenames:
                if not filename.startswith('libexec/'):
                    continue
                self.fix_script_hashbang(os.path.join(build_dir, filename))

    def fix_script_hashbang(self, filename):
        """Replace the hashbangs of a script in libexec."""
        if not os.path.exists(filename):
            return
        with open(filename) as f:
            data = f.read()
        if not data.startswith('#!'):
            return
        lines = data.splitlines()
        if 'python' not in lines[0]:
            return

        lines[0] = '#!%s' % sys.executable
        with open(filename, 'w') as f:
            for line in lines:
                f.write(line)
                f.write('\n')


setup(
    name='pgxnclient',
    description=(
        'A command line tool to interact with the PostgreSQL Extension Network.'
    ),
    long_description=long_description,
    author='Daniele Varrazzo',
    author_email='daniele.varrazzo@gmail.com',
    url='https://github.com/pgxn/pgxnclient',
    project_urls={
        'Source': 'https://github.com/pgxn/pgxnclient',
        'Documentation': 'https://pgxn.github.io/pgxnclient/',
        'Discussion group': 'https://groups.google.com/group/pgxn-users/',
    },
    license='BSD',
    # NOTE: keep consistent with docs/install.txt
    python_requires='>=2.7,!=3.0.*,!=3.1.*,!=3.2.*,!=3.3.*',
    packages=find_packages(),
    package_data={'pgxnclient': ['libexec/*']},
    entry_points={
        'console_scripts': [
            'pgxn = pgxnclient.cli:command_dispatch',
            'pgxnclient = pgxnclient.cli:script',
        ]
    },
    classifiers=[x for x in classifiers.split('\n') if x],
    zip_safe=False,  # because we dynamically look for commands
    install_requires=requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    version=version,
    cmdclass={'build_py': CustomBuildPy},
)
