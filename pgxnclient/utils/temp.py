"""
pgxnclient -- temp files utilities
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client

import shutil
import tempfile
import contextlib

@contextlib.contextmanager
def temp_dir():
    """Context manager to create a temp dir and delete after usage."""
    dir = tempfile.mkdtemp()
    yield dir
    shutil.rmtree(dir)

