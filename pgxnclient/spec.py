"""
pgxnclient -- specification object
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client


import os
import re
import urllib
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
            dirname=None, filename=None, url=None):
        self.name = name and name.lower()
        self.op = op
        self.ver = ver

        # point to local files or specific resources
        self.dirname = dirname
        self.filename = filename
        self.url = url

    def is_name(self):
        return self.name is not None

    def is_dir(self):
        return self.dirname is not None

    def is_file(self):
        return self.filename is not None

    def is_url(self):
        return self.url is not None

    def is_local(self):
        return self.is_dir() or self.is_file()

    def __str__(self):
        name = self.name or self.filename or self.dirname or self.url or "???"
        if self.op is None:
            return name
        else:
            return "%s%s%s" % (name, self.op, self.ver)

    @classmethod
    def parse(self, spec):
        """Parse a spec string into a populated Spec instance.

        Raise BadSpecError if couldn't parse.
        """
        # check if it's a network resource
        if spec.startswith('http://') or spec.startswith('https://'):
            return Spec(url=spec)

        # check if it's a local resource
        if spec.startswith('file://'):
            try_file = urllib.unquote_plus(spec[len('file://'):])
        elif os.sep in spec:
            try_file = spec
        else:
            try_file = None

        if try_file:
            # This is a local thing, let's see what
            if os.path.isdir(try_file):
                return Spec(dirname=try_file)
            elif os.path.exists(try_file):
                return Spec(filename=try_file)
            else:
                raise ResourceNotFound(_("cannot find '%s'") % try_file)

        # so we think it's a PGXN spec

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



