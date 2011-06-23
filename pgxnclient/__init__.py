"""
pgxnclient -- main package
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

__version__ = '0.3dev0'

__all__ = ['Spec', 'SemVer', 'Label', 'Identifier']

from pgxnclient.spec import Spec
from pgxnclient.utils.semver import SemVer
from pgxnclient.utils.label import Label, Identifier


