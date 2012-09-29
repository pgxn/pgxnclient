"""
pgxnclient -- zip file utilities
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client

import os
import stat
import zipfile

from pgxnclient.utils import b
from pgxnclient.i18n import _
from pgxnclient.errors import PgxnClientException
from pgxnclient.archive import Archive

import logging
logger = logging.getLogger('pgxnclient.zip')


class ZipArchive(Archive):
    """Handle .zip archives"""

    _file = None

    def can_open(self):
        return zipfile.is_zipfile(self.filename)

    def open(self):
        assert not self._file, "archive already open"
        try:
            self._file = zipfile.ZipFile(self.filename, 'r')
        except Exception, e:
            raise PgxnClientException(
                _("cannot open archive '%s': %s") % (self.filename, e))

    def close(self):
        if self._file is not None:
            self._file.close()
            self._file = None

    def list_files(self):
        assert self._file, "archive not open"
        return self._file.namelist()

    def read(self, fn):
        assert self._file, "archive not open"
        return self._file.read(fn)

    def unpack(self, destdir):
        zipname = self.filename
        logger.info(_("unpacking: %s"), zipname)
        destdir = os.path.abspath(destdir)
        self.open()
        try:
            for fn in self.list_files():
                fname = os.path.abspath(os.path.join(destdir, fn))
                if not fname.startswith(destdir):
                    raise PgxnClientException(
                        _("archive file '%s' trying to escape!") % fname)

                # Looks like checking for a trailing / is the only way to
                # tell if the file is a directory.
                if fn.endswith('/'):
                    os.makedirs(fname)
                    continue

                # The directory is not always explicitly present in the archive
                if not os.path.exists(os.path.dirname(fname)):
                    os.makedirs(os.path.dirname(fname))

                # Copy the file content
                logger.debug(_("saving: %s"), fname)
                fout = open(fname, "wb")
                try:
                    data = self.read(fn)
                    # In order to restore the executable bit, I haven't find
                    # anything that looks like an executable flag in the zipinfo,
                    # so look at the hashbangs...
                    isexec = data[:2] == b('#!')
                    fout.write(data)
                finally:
                    fout.close()

                if isexec:
                    os.chmod(fname, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)

        finally:
            self.close()

        return self._find_work_directory(destdir)


def unpack(filename, destdir):
    return ZipArchive(filename).unpack(destdir)

