"""
pgxnclient -- test suite package

The test suite can be run via setup.py test. But you better use "make check"
in order to correctly set up the pythonpath.
"""

# Copyright (C) 2011-2019 Daniele Varrazzo

# This file is part of the PGXN client


import unittest


# fix unittest maintainers stubborness: see Python issue #9424
if unittest.TestCase.assert_ is not unittest.TestCase.assertTrue:
    # Vaffanculo, Wolf
    unittest.TestCase.assert_ = unittest.TestCase.assertTrue
    unittest.TestCase.assertEquals = unittest.TestCase.assertEqual


if __name__ == '__main__':
    unittest.main()
