"""
pgxnclient -- main package
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

__version__ = '0.3b1'

# Path where to find the command executables.
# If relative, it's from the `pgxnclient` package directory.
# Distribution packagers may move it to a different directory
# (eventually specifying an absolute path).
LIBEXECDIR = './libexec/'


__all__ = [
    'Spec', 'SemVer', 'Label', 'Term', 'Identifier',
    'get_scripts_dir', 'find_script' ]

import os

from pgxnclient.spec import Spec
from pgxnclient.utils.semver import SemVer
from pgxnclient.utils.strings import Label, Term, Identifier


def get_scripts_dir():
    """
    Return the absolute path of the directory containing the client scripts.
    """
    return os.path.normpath(os.path.join(
        os.path.dirname(__file__), LIBEXECDIR))

def find_script(name):
    """Return the absoulute path of a pgxn script.

    The script are usually found in the `LIBEXEC` dir, but any script on the
    path will do (they are usually prefixed by ``pgxn-``).

    Return `None` if the script is not found.
    """
    path = os.environ.get('PATH', '').split(os.pathsep)
    path.insert(0, get_scripts_dir())
    for p in path:
        fn = os.path.join(p, name)
        if os.path.isfile(fn):
            return fn


