"""
Label -- a valid RFC 1034 identifier
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client


import re

from pgxnclient.i18n import _


class Label(str):
    """A string following the rules in RFC 1034.
    
    Labels can then be used as host names in domains.
    
    http://tools.ietf.org/html/rfc1034

    "The labels must follow the rules for ARPANET host names. They must
    start with a letter, end with a letter or digit, and have as interior
    characters only letters, digits, and hyphen. There are also some
    restrictions on the length. Labels must be 63 characters or less."

    """
    def __new__(cls, value):
        if not Label.re_label.match(value):
            raise ValueError(_("bad label: '%s'") % value)
        return str.__new__(cls, value)

    re_label = re.compile(
        # TODO: quick hack - remove the _ from here!!!
        # I assumed the packages were Label but they aren't
        r'^[a-z]([-a-z0-9_]{0,61}[a-z0-9_])?$',
        re.IGNORECASE)

    def __eq__(self, other):
        if isinstance(other, Label):
            return self.lower() == other.lower()
        else:
            return NotImplemented

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        if isinstance(other, Label):
            return self.lower() < other.lower()
        else:
            return NotImplemented

    def __gt__(self, other):
        return other < self

    def __le__(self, other):
        return not other < self

    def __ge__(self, other):
        return not self < other


