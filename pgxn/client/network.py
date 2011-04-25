"""
pgxn.client -- network interaction
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

import json
import urllib2

from pgxn.client import __version__
from pgxn.client.i18n import _
from pgxn.client.errors import NetworkError, ResourceNotFound, BadRequestError

import logging
logger = logging.getLogger('pgxn.client.network')

def get_file(url):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'pgxn.client/%s' % __version__)]
    logger.debug('opening url: %s', url)
    try:
        return opener.open(url)
    except urllib2.HTTPError, e:
        if e.code == 404:
            raise ResourceNotFound(_("resource not found"))
        elif e.code == 400:
            raise BadRequestError(_("bad request on '%s'") % e.url)
        elif e.code == 500:
            raise NetworkError(_("server error"))
        elif e.code == 503:
            raise NetworkError(_("service unavailable"))
        else:
            raise NetworkError(_("unexpected response %d for '%s'")
                % (e.code, e.url))

def get_json(url):
    return json.load(get_file(url))

def download(url, fn):
    logger.info(_("saving %s"), fn)
    fin = get_file(url)
    fout = open(fn, "wb")
    try:
        while 1:
            data = fin.read(8192)
            if not data: break
            fout.write(data)
    finally:
        fout.close()

