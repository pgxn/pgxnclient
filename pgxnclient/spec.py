"""
pgxnclient -- specification object
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client


import os
import re
import operator as _op

from pgxnclient.i18n import _
from pgxnclient.errors import BadSpecError, ResourceNotFound

from pgxnclient.utils.semver import SemVer
from pgxnclient.utils.strings import Term


class Spec(object):
    """A name together with a range of versions."""

    # Available release statuses.
    # Order matters.
    UNSTABLE = 0
    TESTING = 1
    STABLE = 2

    STATUS = {
        'unstable': UNSTABLE,
        'testing': TESTING,
        'stable': STABLE, }

    def __init__(self, name=None, op=None, ver=None,
            dirname=None, filename=None):
        self.name = name and name.lower()
        self.op = op
        self.ver = ver

        # point to local files
        self.dirname = dirname
        self.filename = filename

    def is_dir(self):
        return self.dirname is not None

    def is_file(self):
        return self.filename is not None

    def is_local(self):
        return self.is_dir() or self.is_file()

    def __str__(self):
        name = self.name or self.filename or self.dirname or "???"
        if self.op is None:
            return name
        else:
            return "%s%s%s" % (name, self.op, self.ver)

    @classmethod
    def parse(self, spec):
        """Parse a spec string into a populated Spec instance.

        Raise BadSpecError if couldn't parse.
        """
        if os.sep in spec:
            # This is a local thing, let's see what
            if os.path.isdir(spec):
                return Spec(dirname=spec)
            elif os.path.exists(spec):
                return Spec(filename=spec)
            else:
                raise ResourceNotFound(_("cannot find '%s'") % spec)

        # split operator/version and name
        m = re.match(r'(.+?)(?:(==|=|>=|>|<=|<)(.*))?$', spec)
        if m is None:
            raise BadSpecError(
                _("bad format for version specification: '%s'"), spec)

        name = Term(m.group(1))
        op = m.group(2)
        if op == '=':
            op = '=='

        if op is not None:
            ver = SemVer.clean(m.group(3))
        else:
            ver = None

        return Spec(name, op, ver)

    def accepted(self, version, _map = {
            '==': _op.eq, '<=': _op.le, '<': _op.lt, '>=': _op.ge, '>': _op.gt}):
        """Return True if the given version is accepted in the spec."""
        if self.op is None:
            return True
        return _map[self.op](version, self.ver)



