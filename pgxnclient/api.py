"""
pgxnclient -- client API stub
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

from urllib import urlencode

from pgxnclient.utils import load_json
from pgxnclient.errors import NetworkError, NotFound, ResourceNotFound
from pgxnclient.network import get_file
from pgxnclient.utils.uri import expand_template


class Api(object):
    def __init__(self, mirror):
        self.mirror = mirror

    def dist(self, dist, version=''):
        try:
            return load_json(self.call(
                version and 'meta' or 'dist',
                {'dist': dist, 'version': version}))
        except ResourceNotFound:
            raise NotFound("distribution '%s' not found" % dist)

    def ext(self, ext):
        try:
            return load_json(self.call('extension', {'extension': ext}))
        except ResourceNotFound:
            raise NotFound("extension '%s' not found" % ext)

    def meta(self, dist, version, as_json=True):
        f = self.call('meta', {'dist': dist, 'version': version})
        if as_json:
            return load_json(f)
        else:
            return f.read().decode('utf-8')

    def readme(self, dist, version):
        return self.call('readme', {'dist': dist, 'version': version}).read()

    def download(self, dist, version):
        dist = dist.lower()
        version = version.lower()
        return self.call('download', {'dist': dist, 'version': version})

    def mirrors(self):
        return load_json(self.call('mirrors'))

    def search(self, where, query):
        """Search into PGXN.

        :param where: where to search. The server currently supports "docs",
            "dists", "extensions"
        :param query: list of strings to search
        """
        # convert the query list into a string
        q = ' '.join([' ' in s and ('"%s"' % s) or s for s in query])

        return load_json(self.call('search', {'in': where},
            query={'q': q}))

    def stats(self, arg):
        return load_json(self.call('stats', {'stats': arg}))

    def user(self, username):
        return load_json(self.call('user', {'user': username}))

    def call(self, meth, args=None, query=None):
        url = self.get_url(meth, args, query)
        return get_file(url)

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
                self._api_index = load_json(get_file(url))
            except ResourceNotFound:
                raise NetworkError("API index not found at '%s'" % url)

        return self._api_index


