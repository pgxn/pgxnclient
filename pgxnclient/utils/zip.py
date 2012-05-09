"""
pgxnclient -- zip file utilities
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

import os
import stat
from zipfile import ZipFile

from pgxnclient.utils import b, load_jsons
from pgxnclient.i18n import _
from pgxnclient.errors import PgxnClientException

import logging
logger = logging.getLogger('pgxnclient.utils.zip')

def unpack(zipname, destdir):
    logger.info(_("unpacking: %s"), zipname)
    destdir = os.path.abspath(destdir)
    zf = ZipFile(zipname, 'r')
    try:
        for fn in zf.namelist():
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
                data = zf.read(fn)
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
        zf.close()

    # Choose the directory where to work. Because we are mostly a wrapper for
    # pgxs, let's look for a makefile. The zip should contain a single base
    # directory, so return the first dir we found containing a Makefile,
    # alternatively just return the unpacked dir
    for dir in os.listdir(destdir):
        for fn in ('Makefile', 'makefile', 'GNUmakefile', 'configure'):
            if os.path.exists(os.path.join(destdir, dir, fn)):
                return os.path.join(destdir, dir)

    return destdir

def get_meta_from_zip(filename):
    try:
        zf = ZipFile(filename, 'r')
    except Exception, e:
        raise PgxnClientException(
            _("cannot open archive '%s': %s") % (filename, e))

    try:
        # Return the first file with the expected name
        for fn in zf.namelist():
            if fn.endswith('META.json'):
                return load_jsons(zf.read(fn).decode('utf8'))
        else:
            raise PgxnClientException(
                _("file 'META.json' not found in archive '%s'") % filename)
    finally:
        zf.close()

