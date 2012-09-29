"""
pgxnclient -- client API stub
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client

from __future__ import with_statement

from urllib import urlencode

from pgxnclient import network
from pgxnclient.utils import load_json
from pgxnclient.errors import NetworkError, NotFound, ResourceNotFound
from pgxnclient.utils.uri import expand_template


class Api(object):
    def __init__(self, mirror):
        self.mirror = mirror

    def dist(self, dist, version=''):
        try:
            with self.call(version and 'meta' or 'dist',
                    {'dist': dist, 'version': version}) as f:
                return load_json(f)
        except ResourceNotFound:
            raise NotFound("distribution '%s' not found" % dist)

    def ext(self, ext):
        try:
            with self.call('extension', {'extension': ext}) as f:
                return load_json(f)
        except ResourceNotFound:
            raise NotFound("extension '%s' not found" % ext)

    def meta(self, dist, version, as_json=True):
        with self.call('meta', {'dist': dist, 'version': version}) as f:
            if as_json:
                return load_json(f)
            else:
                return f.read().decode('utf-8')

    def readme(self, dist, version):
        with self.call('readme', {'dist': dist, 'version': version}) as f:
            return f.read()

    def download(self, dist, version):
        dist = dist.lower()
        version = version.lower()
        return self.call('download', {'dist': dist, 'version': version})

    def mirrors(self):
        with self.call('mirrors') as f:
            return load_json(f)

    def search(self, where, query):
        """Search into PGXN.

        :param where: where to search. The server currently supports "docs",
            "dists", "extensions"
        :param query: list of strings to search
        """
        # convert the query list into a string
        q = ' '.join([' ' in s and ('"%s"' % s) or s for s in query])

        with self.call('search', {'in': where}, query={'q': q}) as f:
            return load_json(f)

    def stats(self, arg):
        with self.call('stats', {'stats': arg}) as f:
            return load_json(f)

    def user(self, username):
        with self.call('user', {'user': username}) as f:
            return load_json(f)

    def call(self, meth, args=None, query=None):
        url = self.get_url(meth, args, query)
        return network.get_file(url)

    def get_url(self, meth, args=None, query=None):
        tmpl = self.get_template(meth)
        url = expand_template(tmpl, args or {})
        url = self.mirror.rstrip('/') + url
        if query is not None:
            url = url + '?' + urlencode(query)

        return url

    def get_template(self, meth):
        return self.get_index()[meth]

    _api_index = None

    def get_index(self):
        if self._api_index is None:
            url = self.mirror.rstrip('/') + '/index.json'
            try:
                with network.get_file(url) as f:
                    self._api_index = load_json(f)
            except ResourceNotFound:
                raise NetworkError("API index not found at '%s'" % url)

        return self._api_index


