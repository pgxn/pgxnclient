"""
pgxnclient -- unit test utilities
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client

import os


def ifunlink(fn):
    """Delete a file if exists."""
    if os.path.exists(fn):
        os.unlink(fn)


_testdata_dir = None

def get_test_filename(*parts):
    """Return the complete file name for a testing file.

    Note: The unit test is currently a pgxnclient sub-package: this is
    required to have it converted to Python 3. However this results in the
    subpackage being installed together with the main package. I don't mind
    that (well, I do, but I don't think can do anything else), but I don't
    want the crap of the test data files added to the package too. So,
    the test files are found wherever are stored in any parent directory of
    this module, which is ok for about any development setup.
    """
    global _testdata_dir
    if _testdata_dir is None:
        _testdata_dir = os.path.dirname(__file__)
        while not os.path.isdir(os.path.join(_testdata_dir, 'testdata')):
            tmp = os.path.dirname(_testdata_dir)
            if not tmp or tmp == _testdata_dir:
                raise ValueError("'testdata' directory not found")
            _testdata_dir = tmp

    return os.path.join(_testdata_dir, 'testdata', *parts)

