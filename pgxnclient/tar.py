"""
pgxnclient -- tar file utilities
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client

import os
import tarfile

from pgxnclient.i18n import _
from pgxnclient.errors import PgxnClientException
from pgxnclient.archive import Archive

import logging
logger = logging.getLogger('pgxnclient.tar')


class TarArchive(Archive):
    """Handle .tar archives"""
    _file = None

    def can_open(self):
        return tarfile.is_tarfile(self.filename)

    def open(self):
        assert not self._file, "archive already open"
        try:
            self._file = tarfile.open(self.filename, 'r')
        except Exception, e:
            raise PgxnClientException(
                _("cannot open archive '%s': %s") % (self.filename, e))

    def close(self):
        if self._file is not None:
            self._file.close()
            self._file = None

    def list_files(self):
        assert self._file, "archive not open"
        return self._file.getnames()

    def read(self, fn):
        assert self._file, "archive not open"
        return self._file.extractfile(fn).read()

    def unpack(self, destdir):
        tarname = self.filename
        logger.info(_("unpacking: %s"), tarname)
        destdir = os.path.abspath(destdir)
        self.open()
        try:
            for fn in self.list_files():
                fname = os.path.abspath(os.path.join(destdir, fn))
                if not fname.startswith(destdir):
                    raise PgxnClientException(
                        _("archive file '%s' trying to escape!") % fname)

            self._file.extractall(path=destdir)
        finally:
            self.close()

        return self._find_work_directory(destdir)


def unpack(filename, destdir):
    return TarArchive(filename).unpack(destdir)

