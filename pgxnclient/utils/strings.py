"""
Strings -- implementation of a few specific string subclasses.
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client


import re

from pgxnclient.i18n import _
from pgxnclient.utils.argparse import ArgumentTypeError


class CIStr(str):
    """
    A case preserving string with non case-sensitive comparison.
    """
    def __eq__(self, other):
        if isinstance(other, CIStr):
            return self.lower() == other.lower()
        else:
            return NotImplemented

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        if isinstance(other, CIStr):
            return self.lower() < other.lower()
        else:
            return NotImplemented

    def __gt__(self, other):
        return other < self

    def __le__(self, other):
        return not other < self

    def __ge__(self, other):
        return not self < other


class Label(CIStr):
    """A string following the rules in RFC 1034.

    Labels can then be used as host names in domains.

    http://tools.ietf.org/html/rfc1034

    "The labels must follow the rules for ARPANET host names. They must
    start with a letter, end with a letter or digit, and have as interior
    characters only letters, digits, and hyphen. There are also some
    restrictions on the length. Labels must be 63 characters or less."

    """
    def __new__(cls, value):
        if not Label._re_chk.match(value):
            raise ValueError(_("bad label: '%s'") % value)
        return CIStr.__new__(cls, value)

    _re_chk = re.compile(
        r'^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$',
        re.IGNORECASE)


class Term(CIStr):
    """
    A Term is a subtype of String that must be at least two characters long
    contain no slash (/), backslash (\), control, or space characters.

    See http://pgxn.org/spec#Term
    """
    def __new__(cls, value):
        if not Term._re_chk.match(value) or min(map(ord, value)) < 32:
            raise ValueError(_("not a valid term term: '%s'") % value)
        return CIStr.__new__(cls, value)

    _re_chk = re.compile( r'^[^\s/\\]{2,}$')


class Identifier(CIStr):
    """
    A string modeling a PostgreSQL identifier.
    """
    def __new__(cls, value):
        if not value:
            raise ValueError("PostgreSQL identifiers cannot be blank")
        if not Identifier._re_chk.match(value):
            value = '"%s"' % value.replace('"', '""')
        # TODO: identifier are actually case sensitive if quoted
        return CIStr.__new__(cls, value)

    _re_chk = re.compile(
        r'^[a-z_][a-z0-9_\$]*$',
        re.IGNORECASE)

    @classmethod
    def parse_arg(self, s):
        """
        Parse an Identifier from a command line argument.
        """
        try:
            return Identifier(s)
        except ValueError, e:
            # shouldn't happen anymore as we quote invalid identifiers
            raise ArgumentTypeError(e)

