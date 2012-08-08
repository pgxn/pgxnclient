"""
pgxnclient -- misc utilities package
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client


__all__ = ['OrderedDict', 'load_json', 'load_jsons', 'sha1', 'b',
    'find_executable']


import sys
import os

# OrderedDict available from Python 2.7
if sys.version_info >= (2, 7):
    from collections import OrderedDict
else:
    from pgxnclient.utils.ordereddict import OrderedDict


# Import the proper JSON library.
#
# Dependencies note: simplejson is certified for Python 2.5.  Support for
# Python 2.4 was available up to version 2.0.9, but this version doesn't
# support ordered dicts. In Py 2.6 the package is in stdlib, but without
# orddict support, so we use simplejson 2.1 again. From Python 2.7 the stdlilb
# json module has orddict support so we don't need the external dependency.
if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

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

