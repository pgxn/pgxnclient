"""
pgxnclient -- test suite package

The test suite can be run via setup.py test. But you better use "make check"
in order to correctly set up the pythonpath.

The test suite relies on the files in the 'testdata' dir, which are currently
not installed but only avaliable in the sdist.
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client


import sys

# import here the unit test module we want to use
if sys.version_info < (2,7):
    import unittest2 as unittest
else:
    import unittest


# fix unittest maintainers stubborness: see Python issue #9424
if unittest.TestCase.assert_ is not unittest.TestCase.assertTrue:
    # Vaffanculo, Wolf
    unittest.TestCase.assert_ = unittest.TestCase.assertTrue
    unittest.TestCase.assertEquals = unittest.TestCase.assertEqual


if __name__ == '__main__':
    unittest.main()

