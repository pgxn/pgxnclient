"""
pgxnclient -- misc utilities package
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client


# Import the proper JSON library
# dependencies note: simplejson is certified for Python 2.5, and supports
# Python 2.4 up to version 2.0.9. After that the package is in the stdlib

import sys
if sys.version_info >= (2, 6):
    import json
else:
    import simplejson as json

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

