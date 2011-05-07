"""
pgxnclient -- informative commands implementation
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

from pgxnclient.i18n import _, N_
from pgxnclient import SemVer
from pgxnclient.errors import ResourceNotFound
from pgxnclient.commands import Command, CommandWithSpec

import logging
logger = logging.getLogger('pgxnclient.commands')


class Mirror(Command):
    name = 'mirror'
    description = N_("return informations about the available mirrors")

    @classmethod
    def customize_parser(self, parser, subparsers, glb, **kwargs):
        subp = self._make_subparser(subparsers)
        subp.add_argument('uri', nargs='?', metavar="URI",
            help = _("return detailed info about this mirror."
                " If not specified return a list of mirror URIs"))
        subp.add_argument('--detailed', action="store_true",
            help = _("return full details for each mirror"))

        return subp

    def run(self):
        data = self.api.mirrors()
        if self.opts.uri:
            detailed = True
            data = [ d for d in data if d['uri'] == self.opts.uri ]
            if not data:
                raise ResourceNotFound(
                    _('mirror not found: %s') % self.opts.uri)
        else:
            detailed = self.opts.detailed

        for i, d in enumerate(data):
            if not detailed:
                print d['uri']
            else:
                for k in [
                "uri", "frequency", "location", "bandwidth", "organization",
                "email", "timezone", "src", "rsync", "notes",]:
                    print "%s: %s" % (k, d.get(k, ''))

                print


class Search(Command):
    name = 'search'
    description = N_("search in the available extensions")

    @classmethod
    def customize_parser(self, parser, subparsers, glb, **kwargs):
        subp = self._make_subparser(subparsers)
        g = subp.add_mutually_exclusive_group()
        g.add_argument('--dist', dest='where', action='store_const',
            const="dists", default='dists',
            help=_("search in distributions [default]"))
        g.add_argument('--ext', dest='where', action='store_const',
            const='extensions',
            help=_("search in extensions"))
        g.add_argument('--docs', dest='where', action='store_const',
            const='docs',
            help=_("search in documentation"))
        subp.add_argument('query', metavar='QUERY',
            help = _("the string to search"))

        return subp

    def run(self):
        data = self.api.search(self.opts.where, self.opts.query)

        for hit in data['hits']:
            print "%s %s" % (hit['dist'], hit['version'])


class Info(CommandWithSpec):
    name = 'info'
    description = N_("print informations about a distribution")

    @classmethod
    def customize_parser(self, parser, subparsers, glb, **kwargs):
        subp = super(Info, self).customize_parser(
            parser, subparsers, glb, **kwargs)

        g = subp.add_mutually_exclusive_group()
        g.add_argument('--details', dest='what',
            action='store_const', const='details', default='details',
            help=_("show details about the distribution [default]"))
        g.add_argument('--meta', dest='what',
            action='store_const', const='meta',
            help=_("show the distribution META.json"))
        g.add_argument('--readme', dest='what',
            action='store_const', const='readme',
            help=_("show the distribution README"))
        g.add_argument('--versions', dest='what',
            action='store_const', const='versions',
            help=_("show the list of available versions"))

        return subp

    def run(self):
        spec = self.get_spec()
        getattr(self, 'print_' + self.opts.what)(spec)

    def print_meta(self, spec):
        data = self.api.dist(spec.name)
        ver = self.get_best_version(data, spec, quiet=True)
        print self.api.meta(spec.name, ver, as_json=False)

    def print_readme(self, spec):
        data = self.api.dist(spec.name)
        ver = self.get_best_version(data, spec, quiet=True)
        print self.api.readme(spec.name, ver)

    def print_details(self, spec):
        data = self.api.dist(spec.name)
        ver = self.get_best_version(data, spec, quiet=True)
        data = self.api.meta(spec.name, ver)
        for k in [u'name', u'abstract', u'description', u'maintainer', u'license',
                u'release_status', u'version', u'date', u'sha1']:
            try:
                v = data[k]
            except KeyError:
                logger.warn(_("data key '%s' not found"), k)
                continue

            if isinstance(v, list):
                for vv in v:
                    print "%s: %s" % (k, vv)
            elif isinstance(v, dict):
                for kk, vv in v.iteritems():
                    print "%s: %s: %s" % (k, kk, vv)
            else:
                print "%s: %s" % (k, v)

        k = 'provides'
        for ext, dext in data[k].iteritems():
            print "%s: %s: %s" % (k, ext, dext['version'])

        k = 'prereqs'
        if k in data:
            for phase, rels in data[k].iteritems():
                for rel, pkgs in rels.iteritems():
                    for pkg, ver in pkgs.iteritems():
                        print "%s: %s: %s %s" % (phase, rel, pkg, ver)

    def print_versions(self, spec):
        data = self.api.dist(spec.name)
        name = data['name']
        vs = [ (SemVer(d['version']), s)
            for s, ds in data['releases'].iteritems()
            for d in ds ]
        vs = [ (v, s) for v, s in vs if spec.accepted(v) ]
        vs.sort(reverse=True)
        for v, s in vs:
            print name, v, s


