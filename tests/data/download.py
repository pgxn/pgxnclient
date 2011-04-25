#!/usr/bin/env python
import sys
from urllib import quote
from urllib2 import urlopen

if __name__ == '__main__':
    url = sys.argv[1]
    fn = quote(url, safe='')
    f = open(fn, "wb")
    try:
        f.write(urlopen(url).read())
    finally:
        f.close()
