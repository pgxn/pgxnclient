"""
pgxnclient -- tar file utilities
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client

import os
import tarfile

from pgxnclient.utils import load_jsons
from pgxnclient.i18n import _
from pgxnclient.errors import PgxnClientException

import logging
logger = logging.getLogger('pgxnclient.utils.tar')

def unpack(tarname, destdir):
    logger.info(_("unpacking: %s"), tarname)
    destdir = os.path.abspath(destdir)
    tf = tarfile.open(tarname, 'r')
    try:
        for fn in tf.getnames():
            if fn.startswith('.') or fn.startswith('/'):
                raise PgxnClientException(_("insecure file name in archive: %s") % fn)

        tf.extractall(path=destdir)
    finally:
        tf.close()

    # Choose the directory where to work. Because we are mostly a wrapper for
    # pgxs, let's look for a makefile. The tar should contain a single base
    # directory, so return the first dir we found containing a Makefile,
    # alternatively just return the unpacked dir
    for dir in os.listdir(destdir):
        for fn in ('Makefile', 'makefile', 'GNUmakefile', 'configure'):
            if os.path.exists(os.path.join(destdir, dir, fn)):
                return os.path.join(destdir, dir)

    return destdir

unpack_tar = unpack # utility alias


def get_meta_from_tar(filename):
    try:
        tf = tarfile.open(filename, 'r')
    except Exception, e:
        raise PgxnClientException(
            _("cannot open archive '%s': %s") % (filename, e))

    try:
        # Return the first file with the expected name
        for fn in tf.getnames():
            if fn.endswith('META.json'):
                return load_jsons(tf.extractfile(fn).read().decode('utf8'))
        else:
            raise PgxnClientException(
                _("file 'META.json' not found in archive '%s'") % filename)
    finally:
        tf.close()

