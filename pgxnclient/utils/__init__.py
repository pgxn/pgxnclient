"""
pgxnclient -- misc utilities package
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client


__all__ = ['OrderedDict', 'load_json', 'load_jsons', 'sha1', 'b']


import sys

# OrderedDict available from Python 2.7
if sys.version_info >= (2, 7):
    from collections import OrderedDict
else:
    from pgxnclient.utils.ordereddict import OrderedDict


# Import the proper JSON library
# dependencies note: simplejson is certified for Python 2.5, and supports
# Python 2.4 up to version 2.0.9. After that the package is in the stdlib
#
# We use json only from 2.7 as it supports ordered dicts. For Python 2.6
# simplejson >= 2.1 should be used.
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
    # order required to keep "provides" extensions in order.
    # Python 2.4 is only compatible with a simplejson version that doesn't
    # support ordered dict.
    if sys.version_info >= (2, 5):
        return json.loads(data, object_pairs_hook=OrderedDict)
    else:
        return json.loads(data)


# Import the sha1 object without warnings
if sys.version_info >= (2, 5):
    from hashlib import sha1
else:
    from sha import new as sha1


# For compatibility from Python 2.4 to 3.x
# b('str') is equivalent to b'str' but works on Python < 2.6 too
if sys.version_info < (3,):
    def b(s):
        return s
else:
    def b(s):
        return s.encode('utf8')

