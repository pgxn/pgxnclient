"""
pgxn.client -- commands module
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

import os
import logging
import argparse

from pgxn.client import __version__
from pgxn.client import Spec, Extension, SemVer
from pgxn.client.api import Api
from pgxn.client.i18n import _, N_, gettext
from pgxn.client.errors import PgxnClientException

logger = logging.getLogger('pgxn.client.commands')

def get_option_parser():
    parser = argparse.ArgumentParser(
        # usage = _("%(prog)s [global options] COMMAND [command options]"),
        description =
            _("Interact with the PostgreSQL Extension Network (PGXN)."),
    )
    parser.add_argument("--version", action='version',
        version="%%(prog)s %s" % __version__,
        help = _("print the version number and exit"))

    glb = parser.add_argument_group(_("Global options"))

    subparsers = parser.add_subparsers(
        title = _("COMMAND"),
        help = _("The command to execute"))

    clss = CommandType.subclasses[:]
    clss.sort(key=lambda c: c.name)
    for cls in clss:
        cls.customize_parser(parser, subparsers, glb)

    return parser

def run_commands(opts, parser):
    # setup the logging
    logging.getLogger().setLevel(
        opts.verbose and logging.DEBUG or logging.INFO)
    return opts.cmd(opts, parser=parser).run()


class CommandType(type):
    subclasses = []
    def __new__(cls, name, bases, dct):
        rv = type.__new__(cls, name, bases, dct)
        CommandType.subclasses.append(rv)
        return rv

    def __init__(cls, name, bases, dct):
        super(CommandType, cls).__init__(name, bases, dct)


class Command(object):
    """
    Base class to implement client commands.

    Provide the argument parsing framework and API dispatch.
    """
    __metaclass__ = CommandType
    name = None
    description = None

    def __init__(self, opts, parser=None):
        """Initialize a new Command.

        The parser will be specified if the class has been initialized
        by that parser itself, so run() can expect it being not None.
        """
        self.opts = opts
        self.parser = parser
        self._api = None

    @classmethod
    def customize_parser(self, parser, subparsers, glb):
        subp = self._make_subparser(subparsers)
        glb.add_argument("--mirror", metavar="URL",
            default = 'http://api.pgxn.org/',
            help = _("the mirror to interact with [default: %(default)s]"))
        glb.add_argument("--verbose", action='store_true',
            help = _("print more informations"))

    def run(self):
        raise NotImplementedError

    @classmethod
    def _make_subparser(self, subparsers, epilog=None):
        # bail out if it is not a subclass being invoked
        if not self.name:
            return
        subp = subparsers.add_parser(self.name,
            help = gettext(self.description),
            epilog = epilog)
        subp.set_defaults(cmd=self)
        return subp

    @property
    def api(self):
        if self._api is None:
            self._api = Api(mirror=self.opts.mirror)

        return self._api

    def get_url(self, fragment):
        return self.opts.mirror.rstrip('/') + fragment


class User(Command):
    name = 'user'
    description = N_("return information about a PGXN user")

    @classmethod
    def customize_parser(self, parser, subparsers, glb):
        subp = self._make_subparser(subparsers)
        subp.add_argument('name', nargs='?', metavar="USERNAME",
            help = _("the user to get details for;"
                " print an users list if not specified"))

    def run(self):
        if not self.opts.name:
            data = self.api.stats('user')
            for u in data['prolific']:
                print (u"%(nickname)s: %(name)s "
                    "(%(dists)d dists, %(releases)d releases)"
                    % u)
        else:
            data = self.api.user(self.opts.name)
            print data


from pgxn.client.errors import ResourceNotFound

class Mirror(Command):
    name = 'mirror'
    description = N_("return info about the mirrors available")

    @classmethod
    def customize_parser(self, parser, subparsers, glb):
        subp = self._make_subparser(subparsers)
        subp.add_argument('uri', nargs='?', metavar="URI",
            help = _("return detailed info about this mirror."
                " If not specified return a list of mirror URIs"))
        subp.add_argument('--detailed', action="store_true",
            help = _("return full details for each mirror"))

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
    description = N_("install an extension into a database")

    @classmethod
    def customize_parser(self, parser, subparsers, glb):
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
        subp.add_argument('query',
            help = _("the string to search"))

    def run(self):
        data = self.api.search(self.opts.where, self.opts.query)

        for hit in data['hits']:
            print "%s %s" % (hit['dist'], hit['version'])


from pgxn.client.errors import BadSpecError

class CommandWithSpec(Command):
    @classmethod
    def customize_parser(self, parser, subparsers, glb):
        # bail out if it is not a subclass being invoked
        if not self.name:
            return

        subp = self._make_subparser(subparsers,
            epilog=_("""
            SPEC can either specify just a name or contain required versions
            indications, for instance 'pkgname=1.0', or 'pkgname>=2.1'.
            """))
        subp.add_argument('spec', metavar='SPEC',
            help = _("name and optional version of the package"))

        g = subp.add_mutually_exclusive_group(required=False)
        g.add_argument('--stable', dest='status',
            action='store_const', const='stable', default='stable',
            help=_("only accept stable distributions [default]"))
        g.add_argument('--testing', dest='status',
            action='store_const', const='testing',
            help=_("accept testing distributions too"))
        g.add_argument('--unstable', dest='status',
            action='store_const', const='unstable',
            help=_("accept unstable distributions too"))

        return subp

    def get_spec(self):
        spec = self.opts.spec
        if spec is None:
            return self._run_recent()

        try:
            spec = Spec.parse(spec)
        except BadSpecError, e:
            self.parser.error(_("cannot parse package '%s': %s")
                % (spec, e))

        if spec.op and spec.op != '==':
            raise NotImplementedError('TODO: operator %s' % op)

        return spec

    def get_best_version(self, data, spec):
        """Return the best version an user may want for a distribution.
        """
        drels = data['releases']
        rels = []
        if 'stable' in drels:
            rels.extend([SemVer(r['version']) for r in drels['stable']])
        if self.opts.status in ('testing', 'unstable') and 'testing' in drels:
            rels.extend([SemVer(r['version']) for r in drels['testing']])
        if self.opts.status == 'unstable' and 'unstable' in drels:
            rels.extend([SemVer(r['version']) for r in drels['unstable']])

        # todo: real filtering
        rels.sort(reverse=True)
        best = rels[0]
        logger.info(_("best version: %s %s"), spec.name, best)
        return best


class Download(CommandWithSpec):
    name = 'download'
    description = N_("download a distribution from the network")

    @classmethod
    def customize_parser(self, parser, subparsers, glb):
        subp = super(Download, self).customize_parser(parser, subparsers, glb)
        subp.add_argument('--target', metavar='PATH', default='.',
            help = _('Target directory and/or filename to save'))

        return subp

    def run(self):
        spec = self.get_spec()
        data = self.api.dist(spec.name)
        ver = self.get_best_version(data, spec)

        fin = self.api.download(spec.name, ver)
        fn = self._get_local_file_name(fin.url)
        logger.info(_("saving %s"), fn)
        fout = open(fn, "wb")
        try:
            while 1:
                data = fin.read(8192)
                if not data: break
                fout.write(data)
        finally:
            fout.close()

        # TODO: verify checksum
        return fn

    def _get_local_file_name(self, url):
        from urlparse import urlsplit
        if os.path.isdir(self.opts.target):
            basename = urlsplit(url)[2].rsplit('/', 1)[-1]
            fn = os.path.join(self.opts.target, basename)
        else:
            fn = self.opts.target

        return os.path.abspath(fn)


import shutil
import tempfile
from zipfile import ZipFile
from subprocess import Popen

class WithUnpacking(object):
    def run(self):
        dir = tempfile.mkdtemp()
        try:
            return self.run_with_temp_dir(dir)
        finally:
            shutil.rmtree(dir)

    def unpack(self, zipname, destdir):
        logger.info(_("unpacking: %s"), zipname)
        destdir = os.path.abspath(destdir)
        zf = ZipFile(zipname, 'r')
        dirout = None
        try:
            for fn in zf.namelist():
                fname = os.path.abspath(os.path.join(destdir, fn))
                if not fname.startswith(destdir):
                    raise PgxnClientException(
                        "archive trying to escape! %s" % fname)
                # TODO: is this the right way to check for dirs?
                if fn.endswith('/'):
                    # Assume we will work in the first dir of the archive
                    if dirout is None:
                        dirout = fname

                    os.makedirs(fname)
                    continue

                logger.debug(_("saving: %s"), fname)
                f = open(fname, "wb")
                try:
                    f.write(zf.read(fn))
                finally:
                    f.close()
        finally:
            zf.close()

        return dirout or destdir


class WithMake(WithUnpacking):
    @classmethod
    def customize_parser(self, parser, subparsers, glb):
        subp = super(WithMake, self).customize_parser(parser, subparsers, glb)

        subp.add_argument('--pg_config', metavar="PATH", default='pg_config',
            help = _("path to the pg_config executable to find the database"
                " [default: %(default)s]"))

    def run_make(self, cmd, dir):
        cmdline = ['make', 'PG_CONFIG=%s' % self.opts.pg_config]
        if cmd == 'installcheck':
            cmdline.append('PGUSER=postgres')

        cmdline.append(cmd)

        cmdline = " ".join(cmdline)
        logger.debug(_("running: %s"), cmdline)
        p = Popen(cmdline, cwd=dir, shell=True)
        p.communicate()
        if p.returncode:
            raise PgxnClientException(
                _("command returned %s") % p.returncode)


class Install(WithMake, CommandWithSpec):
    name = 'install'
    description = N_("install a package")

    def run_with_temp_dir(self, dir):
        self.opts.target = dir
        fn = Download(self.opts).run()
        # TODO: verify checksum
        pdir = self.unpack(fn, dir)

        logger.info(_("building extension"))
        self.run_make('all', dir=pdir)

        logger.info(_("installing extension"))
        self.run_make('install', dir=pdir)


class Check(WithMake, CommandWithSpec):
    name = 'check'
    description = N_("run a distribution's test")

    def run_with_temp_dir(self, dir):
        self.opts.target = dir
        fn = Download(self.opts).run()
        # TODO: verify checksum
        pdir = self.unpack(fn, dir)

        logger.info(_("checking extension"))
        try:
            self.run_make('installcheck', dir=pdir)
        except PgxnClientException, e:
            # if the test failed, copy locally the regression result
            for ext in ('out', 'diffs'):
                fn = os.path.join(pdir, 'regression.' + ext)
                if os.path.exists(fn):
                    logger.info(_('copying regression.%s'), ext)
                    shutil.copy(fn, './regression.' + ext)
            raise

