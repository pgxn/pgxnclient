"""
pgxnclient -- zip file utilities
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

import os
import stat
import shutil
from zipfile import ZipFile

from pgxnclient.utils import json
from pgxnclient.i18n import _
from pgxnclient.errors import PgxnClientException

import logging
logger = logging.getLogger('pgxnclient.utils.zip')

def unpack(zipname, destdir):
    logger.info(_("unpacking: %s"), zipname)
    destdir = os.path.abspath(destdir)
    zf = ZipFile(zipname, 'r')
    dirout = None
    try:
        for fn in zf.namelist():
            fname = os.path.abspath(os.path.join(destdir, fn))
            if not fname.startswith(destdir):
                raise PgxnClientException(
                    _("archive file '%s' trying to escape!") % fname)

            # TODO: is this the right way to check for dirs?
            if fn.endswith('/'):
                # Assume we will work in the first dir of the archive
                if dirout is None:
                    dirout = fname

                os.makedirs(fname)
                continue

            # Copy the file content
            logger.debug(_("saving: %s"), fname)
            fin = zf.open(fn)
            fout = open(fname, "wb")
            try:
                # In order to restore the executable bit, I haven't find
                # anything that looks like an executable file in the zipinfo,
                # so look at the hasbangs...
                data = fin.read(8192)
                isexec = data[:2] == '#!'
                fout.write(data)

                shutil.copyfileobj(fin, fout)
            finally:
                fout.close()

            if isexec:
                os.chmod(fname, stat.S_IREAD | stat.S_IWRITE | stat.S_IEXEC)

    finally:
        zf.close()

    return dirout or destdir

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
                return json.load(zf.open(fn))
        else:
            raise PgxnClientException(
                _("file 'META.json' not found in archive '%s'") % filename)
    finally:
        zf.close()

