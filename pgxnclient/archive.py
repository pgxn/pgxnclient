"""
pgxnclient -- archives handling
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client

import os

from pgxnclient.i18n import _
from pgxnclient.utils import load_jsons
from pgxnclient.errors import PgxnClientException

def from_spec(spec):
    """Return an `Archive` instance to handle the file requested by *spec*
    """
    assert spec.is_file()
    return from_file(spec.filename)

def from_file(filename):
    """Return an `Archive` instance to handle the file *filename*
    """
    # Get the metadata from an archive file
    if filename.endswith('.zip'):
        from pgxnclient.utils.zip import ZipArchive
        return ZipArchive(filename)
    else:
        # Tar files have many naming variants.  Let's not
        # guess them.
        from pgxnclient.utils.tar import TarArchive
        return TarArchive(filename)


class Archive(object):
    """Base class to handle archives."""
    def __init__(self, filename):
        self.filename = filename

    def open(self):
        """Open the archive for usage.

        Raise PgxnClientException if the archive can't be open.
        """
        raise NotImplementedError

    def close(self):
        """Close the archive after usage."""
        raise NotImplementedError

    def list_files(self):
        """Return an iterable with the list of file names in the archive."""
        raise NotImplementedError

    def read(self, fn):
        """Return a file's data from the archive."""
        raise NotImplementedError

    def unpack(self, destdir):
        raise NotImplementedError

    def get_meta(self):
        filename = self.filename

        self.open()
        try:
            # Return the first file with the expected name
            for fn in self.list_files():
                if fn.endswith('META.json'):
                    return load_jsons(self.read(fn).decode('utf8'))
            else:
                raise PgxnClientException(
                    _("file 'META.json' not found in archive '%s'") % filename)
        finally:
            self.close()

    def _find_work_directory(self, destdir):
        """
        Choose the directory where to work.

        Because we are mostly a wrapper for pgxs, let's look for a makefile.
        The tar should contain a single base directory, so return the first
        dir we found containing a Makefile, alternatively just return the
        unpacked dir
        """
        for dir in os.listdir(destdir):
            for fn in ('Makefile', 'makefile', 'GNUmakefile', 'configure'):
                if os.path.exists(os.path.join(destdir, dir, fn)):
                    return os.path.join(destdir, dir)

        return destdir


