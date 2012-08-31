"""
pgxnclient -- archives handling
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client

from pgxnclient.utils.tar import unpack_tar, get_meta_from_tar
from pgxnclient.utils.zip import unpack_zip, get_meta_from_zip


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
        return ZipArchive(filename)
    else:
        # Tar files have many naming variants.  Let's not
        # guess them.
        return TarArchive(filename)


class Archive(object):
    """Base class to handle archives."""
    def __init__(self, filename):
        self.filename = filename

    def get_meta(self):
        raise NotImplementedError

    def unpack(self, destdir):
        raise NotImplementedError


class TarArchive(Archive):
    """Handle .tar archives"""
    def get_meta(self):
        return get_meta_from_tar(self.filename)

    def unpack(self, destdir):
        return unpack_tar(self.filename, destdir)


class ZipArchive(Archive):
    """Handle .zip archives"""
    def get_meta(self):
        return get_meta_from_zip(self.filename)

    def unpack(self, destdir):
        return unpack_zip(self.filename, destdir)


