"""
SemVer -- (not quite) semantic version specification

http://semver.org/

IMPORTANT: don't trust this implementation. And don't trust SemVer AT ALL.
We have a bloody mess because the specification changed after being published
and after several extension had been uploaded with a version number that
suddenly had become no more valid.

https://github.com/mojombo/semver.org/issues/49

My plea for forking the spec and keep our schema has been ignored. So this
module only tries to make sure people can use PGXN, not to be conform to an
half-aborted specification.  End of rant.

This implementation is conform to the SemVer 0.3.0 implementation by David
Wheeler (http://pgxn.org/dist/semver/0.3.0/) and passes all its unit test.

Note that it is slightly non conform to the original specification, as the
trailing part should be compared in ascii order while our comparison is not
case sensitive. David has already stated that the meaning is independent on
the case (http://blog.pgxn.org/post/4948135198/case-insensitivity) and I'm
fine with that: the important thing is that the client and the server
understand each other.

"""

# Copyright (C) 2011-2019 Daniele Varrazzo

# This file is part of the PGXN client

import re
import operator

from pgxnclient.i18n import _


class SemVer(str):
    """A string representing a semantic version number.

    Non valid version numbers raise ValueError.
    """

    def __new__(cls, value):
        self = str.__new__(cls, value)
        self.tuple = SemVer.parse(value)
        return self

    @property
    def major(self):
        return self.tuple[0]

    @property
    def minor(self):
        return self.tuple[1]

    @property
    def patch(self):
        return self.tuple[2]

    @property
    def trail(self):
        return self.tuple[3]

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, str(self))

    def __eq__(self, other):
        if isinstance(other, SemVer):
            return (
                self.tuple[:3] == other.tuple[:3]
                and self.tuple[3].lower() == other.tuple[3].lower()
            )
        elif isinstance(other, str):
            return self == SemVer(other)
        else:
            return NotImplemented

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return hash(self.tuple[:3] + (self.tuple[3].lower(),))

    def _ltgt(self, other, op):
        if isinstance(other, SemVer):
            t1 = self.tuple[:3]
            t2 = other.tuple[:3]
            if t1 != t2:
                return op(t1, t2)

            s1 = self.tuple[3].lower()
            s2 = other.tuple[3].lower()
            if s1 == s2:
                return False
            if s1 and s2:
                return op(s1, s2)
            return op(bool(s2), bool(s1))

        elif isinstance(other, str):
            return op(self, SemVer(other))
        else:
            return NotImplemented

    def __lt__(self, other, op=operator.lt):
        return self._ltgt(other, operator.lt)

    def __gt__(self, other):
        return self._ltgt(other, operator.gt)

    def __ge__(self, other):
        return not self < other

    def __le__(self, other):
        return not other < self

    @classmethod
    def parse(self, s):
        """
        Split a valid version number in components (major, minor, patch, trail).
        """
        m = re_semver.match(s)
        if m is None:
            raise ValueError(_("bad version number: '%s'") % s)

        maj, min, patch, trail = m.groups()
        if not patch:
            patch = 0
        if not trail:
            trail = ''
        return (int(maj), int(min), int(patch), trail)

    @classmethod
    def clean(self, s):
        """
        Convert an invalid but still recognizable version number into a SemVer.
        """
        m = re_clean.match(s.strip())
        if m is None:
            raise ValueError(_("bad version number: '%s' - can't clean") % s)

        maj, min, patch, trail = m.groups()
        maj = maj and int(maj) or 0
        min = min and int(min) or 0
        patch = patch and int(patch) or 0
        trail = trail and '-' + trail.strip() or ''
        return "%d.%d.%d%s" % (maj, min, patch, trail)


re_semver = re.compile(
    r"""
    ^
        (0|[1-9][0-9]*)
    \.  (0|[1-9][0-9]*)
    \.  (0|[1-9][0-9]*)
    (?:
        -?                       # should be mandatory, but see rant above
        ([a-z][a-z0-9-]*)
    )?
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)

re_clean = re.compile(
    r"""
    ^
        ([0-9]+)?
    \.? ([0-9]+)?
    \.? ([0-9]+)?
    (?:
        -?  \s*
        ([a-z][a-z0-9-]*)
    )?
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)
