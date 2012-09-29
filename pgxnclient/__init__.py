"""
pgxnclient -- main package
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client

__version__ = '1.2'

# Paths where to find the command executables.
# If relative, it's from the `pgxnclient` package directory.
# Distribution packagers may move them around if they wish.
#
# Only one of the paths should be marked as "public": it will be returned by
# pgxn help --libexec
LIBEXECDIRS = [
    # public, path
    (False, './libexec/'),
    (True,  '/usr/local/libexec/pgxnclient/'),
    ]


assert len([x for x in LIBEXECDIRS if x[0]]) == 1, \
    "only one libexec directory should be public"

__all__ = [
    'Spec', 'SemVer', 'Label', 'Term', 'Identifier',
    'get_scripts_dirs', 'get_public_script_dir', 'find_script' ]

import os

from pgxnclient.spec import Spec
from pgxnclient.utils.semver import SemVer
from pgxnclient.utils.strings import Label, Term, Identifier


def get_scripts_dirs():
    """
    Return the absolute path of the directories containing the client scripts.
    """
    return [ os.path.normpath(os.path.join(
            os.path.dirname(__file__), p))
        for (_, p) in LIBEXECDIRS ]

def get_public_scripts_dir():
    """
    Return the absolute path of the public directory for the client scripts.
    """
    return [ os.path.normpath(os.path.join(
            os.path.dirname(__file__), p))
        for (public, p) in LIBEXECDIRS if public ][0]

def find_script(name):
    """Return the absoulute path of a pgxn script.

    The script are usually found in the `LIBEXEC` dir, but any script on the
    path will do (they are usually prefixed by ``pgxn-``).

    Return `None` if the script is not found.
    """
    path = os.environ.get('PATH', '').split(os.pathsep)
    path[0:0] = get_scripts_dirs()
    for p in path:
        fn = os.path.join(p, name)
        if os.path.isfile(fn):
            return fn


