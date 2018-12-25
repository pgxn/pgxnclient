"""
pgxnclient -- misc utilities package
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client


__all__ = ['OrderedDict', 'load_json', 'load_jsons', 'sha1', 'b',
    'find_executable']


import os
import sys
import json
from collections import OrderedDict


def load_json(f):
    data = f.read()
    if not isinstance(data, unicode):
        data = data.decode('utf-8')
    return load_jsons(data)

def load_jsons(data):
    return json.loads(data, object_pairs_hook=OrderedDict)


# Import the sha1 object without warnings
from hashlib import sha1


# For compatibility from Python 2.4 to 3.x
# b('str') is equivalent to b'str' but works on Python < 2.6 too
if sys.version_info < (3,):
    def b(s):
        return s
else:
    def b(s):
        return s.encode('utf8')


def find_executable(name):
    """
    Find executable by ``name`` by inspecting PATH environment variable, return
    ``None`` if nothing found.
    """
    for dir in os.environ.get('PATH', '').split(os.pathsep):
        if not dir:
            continue
        fn = os.path.abspath(os.path.join(dir, name))
        if os.path.exists(fn):
            return os.path.abspath(fn)

