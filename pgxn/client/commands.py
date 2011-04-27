"""
pgxn.client -- commands module
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

import os
import logging
from pgxn.utils import argparse

from pgxn.client import __version__
from pgxn.client import Spec, Extension, Label, SemVer
from pgxn.client.api import Api
from pgxn.client.i18n import _, N_, gettext
from pgxn.client.errors import PgxnClientException, UserAbort
from pgxn.client.network import download

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
        glb.add_argument("--yes", action='store_true',
            help = _("assume affermative answer to all questions"))

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

    def confirm(self, prompt):
        if self.opts.yes:
            return True

        while 1:
            ans = raw_input(_("%s [y/N] ") % prompt)
            if _('no').startswith(ans.lower()):
                raise UserAbort(_("operation interrupted on user request"))
            elif _('yes').startswith(ans.lower()):
                return True
            else:
                prompt = _("Please answer yes or no")


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

        try:
            spec = Spec.parse(spec)
        except BadSpecError, e:
            self.parser.error(_("cannot parse package '%s': %s")
                % (spec, e))

        return spec

    def get_best_version(self, data, spec):
        """Return the best version an user may want for a distribution.
        """
        drels = data['releases']
        vers = []
        if 'stable' in drels:
            vers.extend([SemVer(r['version']) for r in drels['stable']])
        if self.opts.status in ('testing', 'unstable') and 'testing' in drels:
            vers.extend([SemVer(r['version']) for r in drels['testing']])
        if self.opts.status == 'unstable' and 'unstable' in drels:
            vers.extend([SemVer(r['version']) for r in drels['unstable']])

        vers.sort(reverse=True)
        for ver in vers:
            if spec.accepted(ver):
                logger.info(_("best version: %s %s"), spec.name, ver)
                return ver
        else:
            raise ResourceNotFound(
                _("no suitable version found for extension '%s'"
                    " (release level: %s)" % (spec.name, self.opts.status)))


from pgxn.utils import sha1
from pgxn.client.errors import BadChecksum

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

        try:
            chk = data['sha1']
        except KeyError:
            raise PgxnClientException(
                "sha1 missing from the distribution meta")

        fin = self.api.download(spec.name, ver)
        fn = self._get_local_file_name(fin.url)
        fn = download(fin, fn, rename=True)
        self.verify_checksum(fn, chk)
        return fn

    def verify_checksum(self, fn, chk):
        """Verify that a downloaded file has the expected sha1."""
        sha = sha1()
        logger.debug(_("checking sha1 of '%s'"), fn)
        f = open(fn, "rb")
        try:
            while 1:
                data = f.read(8192)
                if not data: break
                sha.update(data)
        finally:
            f.close()

        sha = sha.hexdigest()
        if sha != chk:
            os.unlink(fn)
            logger.error(_("file %s has sha1 %s instead of %s"),
                fn, sha, chk)
            raise BadChecksum(_("bad sha1 in downloaded file"))

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
from subprocess import Popen, PIPE

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


class WithPgConfig(object):
    @classmethod
    def customize_parser(self, parser, subparsers, glb):
        subp = super(WithPgConfig, self).customize_parser(
            parser, subparsers, glb)

        subp.add_argument('--pg_config', metavar="PATH", default='pg_config',
            help = _("path to the pg_config executable to find the database"
                " [default: %(default)s]"))

    def call_pg_config(self, what, _cache={}):
        if what in _cache:
            return _cache[what]

        cmdline = "%s --%s" % (self.opts.pg_config, what)
        logger.debug("running pg_config with: %s", cmdline)
        p = Popen(cmdline, stdout=PIPE, shell=True)
        out, err = p.communicate()
        if p.returncode:
            raise PgxnClientException(
                "%s returned %s" % (cmdline, p.returncode))

        rv = _cache[what] = out.rstrip()
        return rv


class WithMake(WithPgConfig, WithUnpacking):
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
    description = N_("install a distribution")

    def run_with_temp_dir(self, dir):
        self.opts.target = dir
        fn = Download(self.opts).run()
        pdir = self.unpack(fn, dir)

        self.maybe_run_configure(pdir)

        logger.info(_("building extension"))
        self.run_make('all', dir=pdir)

        logger.info(_("installing extension"))
        self.run_make('install', dir=pdir)

    def maybe_run_configure(self, dir):
        fn = os.path.join(dir, 'configure')
        logger.debug("checking '%s'", fn)
        # TODO: probably not portable
        if not os.path.exists(fn):
            return

        logger.info(_("running configure"))
        p = Popen(fn)
        p.communicate()
        if p.returncode:
            raise PgxnClientException(
                _("configure failed with return code %s") % p.returncode)


class Check(WithMake, CommandWithSpec):
    name = 'check'
    description = N_("run a distribution's test")

    def run_with_temp_dir(self, dir):
        self.opts.target = dir
        fn = Download(self.opts).run()
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


class WithDatabase(object):
    @classmethod
    def customize_parser(self, parser, subparsers, glb):
        subp = super(WithDatabase, self).customize_parser(
            parser, subparsers, glb)

        g = subp.add_argument_group(_("Database connections options"))

        g.add_argument('-d', '--dbname', metavar="DBNAME",
            help = _("database name to install into"))
        g.add_argument('-h', '--host', metavar="HOST",
            help = _("database server host or socket directory"))
        g.add_argument('-p', '--port', metavar="PORT", type=int,
            help = _("database server port"))
        g.add_argument('-U', '--username', metavar="NAME",
            help = _("database user name"))

        subp.epilog += _("""
The default database connection options depend on the value of environment
variables PGDATABASE, PGHOST, PGPORT, PGUSER.
""")
        return subp

    def get_psql_options(self):
        """
        Return the cmdline options to connect to the specified database.
        """
        rv = []

        if self.opts.dbname:
            rv.extend(['--dbname', self.opts.dbname])
        if self.opts.host:
            rv.extend(['--host', self.opts.host])
        if self.opts.port:
            rv.extend(['--port', str(self.opts.port)])
        if self.opts.username:
            rv.extend(['--username', self.opts.username])

        return rv


class Load(WithPgConfig, WithDatabase, CommandWithSpec):
    name = 'load'
    description = N_('load the extensions in a distribution into a database')

    def run(self):
        spec = self.get_spec()
        data = self.api.dist(spec.name)
        ver = self.get_best_version(data, spec)
        # TODO: this can be avoided if installing the last version
        dist = self.api.dist(spec.name, ver)

        # TODO: probably unordered before Python 2.7 or something
        for name, data in dist['provides'].items():
            sql = data.get('file')
            self.load_ext(name, sql)

    def load_ext(self, name, sqlfile):
        pgver = self.get_pg_version()
        logger.debug("PostgreSQL version: %d.%d.%d", *pgver)

        if pgver >= (9,1,0):
            if self.is_extension(name):
                self.create_extension(name)
                return
            else:
                self.confirm(_("""\
The extension '%s' doesn't contain a control file:
it will be installed as a loose set of objects.
Do you want to continue?""")
                    % name)

        confirm = False
        if not sqlfile:
            sqlfile = name + '.sql'
            confirm = True

        fn = self.find_sql_file(name, sqlfile)
        if confirm:
            self.confirm(_("""\
The extension '%s' doesn't specify a SQL file.
'%s' is probably the right one.
Do you want to load it?""")
                % (name, fn))

        self.load_sql(fn)


    def get_pg_version(self):
        data = self.call_psql('SELECT version();')
        return self.parse_pg_version(data)

    def parse_pg_version(self, data):
        import re
        m = re.match(r'\S+\s+(\d+)\.(\d+)(?:\.(\d+))?', data)
        if m is None:
            raise PgxnClientException(
                "cannot parse version number from '%s'" % data)

        return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 0))

    def is_extension(self, name):
        fn = os.path.join(self.call_pg_config('sharedir'),
            "extension", name + ".control")
        logger.debug("checking if exists %s", fn)
        return os.path.exists(fn)

    def create_extension(self, name):
        # TODO: namespace etc.
        cmd = "CREATE EXTENSION %s;" % Label(name)
        self.load_sql(data=cmd)

    def call_psql(self, command):
        cmdline = [self.find_psql()]
        cmdline.extend(self.get_psql_options())
        if command is not None:
            cmdline.append('-tA')   # tuple only, unaligned
            cmdline.extend(['-c', command])

        logger.debug("calling %s", cmdline)
        p = Popen(cmdline, stdout=PIPE)
        out, err = p.communicate()
        if p.returncode:
            raise PgxnClientException(
                "psql returned %s running command" % (p.returncode))

        return out

    def load_sql(self, filename=None, data=None):
        cmdline = [self.find_psql()]
        cmdline.extend(self.get_psql_options())
        # load via pipe to enable psql commands in the file
        if not data:
            fin = open(filename, 'r')
            p = Popen(cmdline, stdin=fin)
            p.communicate()
        else:
            p = Popen(cmdline, stdin=PIPE)
            p.communicate(data)

        if p.returncode:
            raise PgxnClientException(
                "psql returned %s loading extension" % (p.returncode))

    def find_psql(self):
        return self.call_pg_config('bindir') + '/psql'

    def find_sql_file(self, name, sqlfile):
        # In the extension the sql can be specified with a directory,
        # butit gets flattened into the target dir by the Makefile
        sqlfile = os.path.basename(sqlfile)

        sharedir = self.call_pg_config('sharedir')
        # TODO: we only check in contrib and in <name>: actually it may be
        # somewhere else - only the makefile knows!
        tries = [
            name + '/' + sqlfile,
            sqlfile.rsplit('.', 1)[0] + '/' + sqlfile,
            'contrib/' + sqlfile,
        ]
        tried = set()
        for fn in tries:
            if fn in tried:
                continue
            tried.add(fn)
            fn = sharedir + '/' + fn
            logger.debug("checking sql file in %s" % fn)
            if os.path.exists(fn):
                return fn
        else:
            raise PgxnClientException(
                "cannot find sql file for extension '%s': '%s'"
                % (name, sqlfile))


