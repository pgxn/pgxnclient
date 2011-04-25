"""
pgxn.client -- client API stub
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

import json
from uri import expand_template
from urllib import urlencode

from pgxn.client.network import get_file

class Api(object):
    def __init__(self, mirror):
        self.mirror = mirror

    def dist(self, name):
        return json.load(self.call('dist', {'dist': name}))

    def download(self, dist, version):
        return self.call('download', {'dist': dist, 'version': version})

    def mirrors(self):
        return json.load(self.call('mirrors'))

    def search(self, where, query):
        return json.load(self.call('search', {'in': where},
            query={'q': query}))

    def stats(self, arg):
        return json.load(self.call('stats', {'stats': arg}))

    def user(self, username):
        return json.load(self.call('user', {'user': username}))

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
        tmpl = self.get_index()[meth]

        # TODO: broken API?
        if meth == 'search':
            tmpl = tmpl.rstrip('/')

        return tmpl

    _api_index = None

    def get_index(self):
        if self._api_index is None:
            url = self.mirror.rstrip('/') + '/index.json'
            self._api_index = json.load(get_file(url))

        return self._api_index


