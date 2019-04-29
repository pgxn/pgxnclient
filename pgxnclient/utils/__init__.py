"""
pgxnclient -- misc utilities package
"""

# Copyright (C) 2011-2019 Daniele Varrazzo

# This file is part of the PGXN client


from __future__ import print_function

__all__ = ['emit', 'load_json', 'load_jsons', 'sha1', 'find_executable']


import os
import sys
import json
from collections import OrderedDict

# Import the sha1 object without warnings
from hashlib import sha1

import six


def emit(s=b'', file=None):
    """
    Print a string

    Easy yes? No. Because if the string is unicode and we are piping stdout
    into something we end up with sys.stdout.encoding = None and Python trying
    to use ascii to encode, barfing on the first accented letter (hello Jan).
    """
    if file is None:
        file = sys.stdout

    enc = file.encoding or 'ascii'

    if isinstance(s, six.text_type):
        s = s.encode(enc, 'replace')

    # OTOH, printing bytes on Py3 to stdout/stderr will barf as well...
    # It's facepalms all the way down.
    if hasattr(file, 'buffer'):
        file = file.buffer

    file.write(s)
    file.write(b'\n')


def load_json(f):
    data = f.read()
    if not isinstance(data, six.text_type):
        data = data.decode('utf-8')
    return load_jsons(data)


def load_jsons(data):
    return json.loads(data, object_pairs_hook=OrderedDict)


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
