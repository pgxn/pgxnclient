"""
pgxnclient -- unit test utilities
"""

# Copyright (C) 2011-2019 Daniele Varrazzo

# This file is part of the PGXN client

import os


def ifunlink(fn):
    """Delete a file if exists."""
    if os.path.exists(fn):
        os.unlink(fn)


def get_test_filename(*parts):
    """Return the complete file name for a testing file.
    """
    return os.path.join(os.path.dirname(__file__), 'testdata', *parts)
