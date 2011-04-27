"""
pgxn.client -- main package
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

__version__ = '0.1dev0'


import re

from pgxn.client.errors import BadSpecError

from pgxn.utils.semver import SemVer

class Name(str):
    """A string representing a package name."""
    # TODO: range

class Spec(object):
    """A name together with a range of versions."""
    def __init__(self, name, op=None, ver=None):
        self.name = name
        self.op = op
        self.ver = ver

    @classmethod
    def parse(self, spec):
        """Parse a spec string and return name and version required.

        Return (name, op, version), op and version can be None.
        Raise BadSpecError if couldn't parse.
        """
        # split operator/version and name
        m = re.match(r'(.+?)(?:(==|=|>=|>|<=|<)(.*))?$', spec)
        if m is None:
            raise BadSpecError('bad format')

        name = Name(m.group(1))
        op = m.group(2)
        if op == '=':
            op = '=='

        if op is not None:
            ver = SemVer(m.group(3))
        else:
            ver = None

        return Spec(name, op, ver)


class Extension(object):
    def __init__(self, name=None, version=None, status=None, abstract=None):
        self.name = name
        self.version = version
        self.status = status
        self.abstract = abstract

    @classmethod
    def from_json(self, data):
        data1 = data[data['latest']]
        name = data['extension']
        abstract = data1.get('abstract')

        rv = []
        for ver, vdata in data['versions'].iteritems():
            vdata = vdata[0]
            ver = SemVer(ver)
            ext = Extension(name=name, version=ver,
                status=vdata.get('status', 'stable'),
                abstract=abstract)
            rv.append(ext)

        rv.sort(key=lambda x: x.version, reverse=True)
        return rv

