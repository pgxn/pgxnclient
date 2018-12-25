#!/usr/bin/env python
"""Download an URL and save it with tne name as the urlquoted url.

The files downloaded are used by the test suite.
"""
import os
import sys
from six.moves.urllib.parse import quote
from six.moves.urllib.request import urlopen

if __name__ == '__main__':
    url = sys.argv[1]
    fn = quote(url, safe='')
    f = open(fn, "wb")
    try:
        try:
            f.write(urlopen(url).read())
        finally:
            f.close()
    except Exception:
        os.unlink(fn)
        raise
