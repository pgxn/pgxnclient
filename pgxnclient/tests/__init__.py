"""
pgxnclient -- test suite package

The test suite can be run via setup.py test. But you better use "make check"
in order to correctly set up the pythonpath.

The test suite relies on the files in the 'testdata' dir, which are currently
not installed but only avaliable in the sdist.
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client


import sys

# import here the unit test module we want to use
if sys.version_info < (2,7):
    import unittest2 as unittest
else:
    import unittest


if __name__ == '__main__':
    unittest.main()

