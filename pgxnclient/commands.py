"""
pgxnclient -- commands module
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

import os
import logging
from pgxnclient.utils import json
from pgxnclient.utils import argparse

from pgxnclient import __version__
from pgxnclient import Spec, Label, SemVer
from pgxnclient.api import Api
from pgxnclient.i18n import _, N_, gettext
from pgxnclient.errors import PgxnClientException, UserAbort
from pgxnclient.network import download

logger = logging.getLogger('pgxnclient.commands')

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

    clss = [ cls for cls in CommandType.subclasses if cls.name ]
    clss.sort(key=lambda c: c.name)
    clss.insert(0, Command)
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
    def customize_parser(self, parser, subparsers, glb, **kwargs):
        subp = self._make_subparser(subparsers)
        glb.add_argument("--mirror", metavar="URL",
            default = 'http://api.pgxn.org/',
            help = _("the mirror to interact with [default: %(default)s]"))
        glb.add_argument("--verbose", action='store_true',
            help = _("print more informations"))
        glb.add_argument("--yes", action='store_true',
            help = _("assume affermative answer to all questions"))

        return subp

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


from pgxnclient.errors import ResourceNotFound

class Mirror(Command):
    name = 'mirror'
    description = N_("return info about the mirrors available")

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
        subp.add_argument('query',
            help = _("the string to search"))

        return subp

    def run(self):
        data = self.api.search(self.opts.where, self.opts.query)

        for hit in data['hits']:
            print "%s %s" % (hit['dist'], hit['version'])


from pgxnclient.errors import BadSpecError
from pgxnclient.utils.zip import get_meta_from_zip

class CommandWithSpec(Command):
    # TODO: the spec should possibly be a local file or a full url
    @classmethod
    def customize_parser(self, parser, subparsers, glb,
            with_status=True, can_be_local=False, **kwargs):
        # bail out if it is not a subclass being invoked
        if not self.name:
            return

        epilog=_("""
SPEC can either specify just a name or contain required versions
indications, for instance 'pkgname=1.0', or 'pkgname>=2.1'.
""")

        if can_be_local:
            epilog += _("""
SPEC may also be a local zip file or unpacked directory, but in this case
it should contain at least a '%s', for instance '.%spkgname.zip'.
""") % (os.sep, os.sep)

        subp = self._make_subparser(subparsers, epilog=epilog)
        subp.add_argument('spec', metavar='SPEC',
            help = _("name and optional version of the package"))

        if with_status:
            g = subp.add_mutually_exclusive_group(required=False)
            g.add_argument('--stable', dest='status',
                action='store_const', const=Spec.STABLE, default=Spec.STABLE,
                help=_("only accept stable distributions [default]"))
            g.add_argument('--testing', dest='status',
                action='store_const', const=Spec.TESTING,
                help=_("accept testing distributions too"))
            g.add_argument('--unstable', dest='status',
                action='store_const', const=Spec.UNSTABLE,
                help=_("accept unstable distributions too"))

        return subp

    def get_spec(self, can_be_local=False):
        spec = self.opts.spec

        try:
            spec = Spec.parse(spec)
        except (ValueError, BadSpecError), e:
            self.parser.error(_("cannot parse package '%s': %s")
                % (spec, e))

        if not can_be_local and spec.is_local():
            raise PgxnClientException(
                _("you cannot use a local resource with this command"))

        return spec

    def get_best_version(self, data, spec):
        """Return the best version an user may want for a distribution.
        """
        drels = data['releases']

        # Get the maximum version for each release status satisfying the spec
        vers = [ None ] * len(Spec.STATUS)
        for n, d in drels.iteritems():
            lvl = Spec.STATUS[n]
            vs = filter(spec.accepted, [SemVer(r['version']) for r in d])
            if vs:
                vers[Spec.STATUS[n]] = max(vs)

        # Is there any result at the desired release status?
        want = [ v for lvl, v in enumerate(vers)
            if lvl >= self.opts.status and v is not None ] 
        if want:
            ver = max(want)
            logger.info(_("best version: %s %s"), spec.name, ver)
            return ver

        # Not found: is there any hint we can give?
        if self.opts.status > Spec.TESTING and vers[Spec.TESTING]:
            hint = (vers[Spec.TESTING], _('testing'))
        elif self.opts.status > Spec.UNSTABLE and vers[Spec.UNSTABLE]:
            hint = (vers[Spec.UNSTABLE], _('unstable'))
        else:
            hint = None

        msg = _("no suitable version found for %s") % spec
        if hint:
            msg += _(" but there is version %s at level %s") % hint

        raise ResourceNotFound(msg)

    def get_meta(self, spec):
        if not spec.is_local():
            # Get the metadata from the API
            data = self.api.dist(spec.name)
            ver = self.get_best_version(data, spec)
            return self.api.meta(spec.name, ver)

        elif spec.is_dir():
            # Get the metadata from a directory
            fn = os.path.join(spec.dirname, 'META.json')
            logger.debug("reading %s", fn)
            if not os.path.exists(fn):
                raise PgxnClientException(
                    _("file 'META.json' not found in '%s'") % dir)

            return json.load(open(fn))

        elif spec.is_file():
            # Get the metadata from a zip file
            return get_meta_from_zip(spec.filename)


class List(CommandWithSpec):
    name = 'list'
    description = N_("list the available versions of a distribution")

    @classmethod
    def customize_parser(self, parser, subparsers, glb, **kwargs):
        subp = super(List, self).customize_parser(parser, subparsers, glb,
            with_status=False, **kwargs)

        return subp

    def run(self):
        spec = self.get_spec()
        data = self.api.dist(spec.name)
        name = data['name']
        vs = [ (SemVer(d['version']), s)
            for s, ds in data['releases'].iteritems()
            for d in ds ]
        vs = [ (v, s) for v, s in vs if spec.accepted(v) ]
        vs.sort(reverse=True)
        for v, s in vs:
            print name, v, s


class Info(CommandWithSpec):
    name = 'info'
    description = N_("obtain informations about a distribution")

    @classmethod
    def customize_parser(self, parser, subparsers, glb, **kwargs):
        subp = super(Info, self).customize_parser(
            parser, subparsers, glb, **kwargs)

        g = subp.add_mutually_exclusive_group()
        g.add_argument('--details', dest='what', action='store_const',
            const='details', default='details',
            help=_("show details about the distribution [default]"))
        g.add_argument('--meta', dest='what', action='store_const', const='meta',
            help=_("show the distribution META.json"))
        g.add_argument('--readme', dest='what', action='store_const', const='readme',
            help=_("show the distribution README"))

        return subp

    def run(self):
        spec = self.get_spec()
        data = self.api.dist(spec.name)
        ver = self.get_best_version(data, spec)
        getattr(self, 'print_' + self.opts.what)(spec, ver)

    def print_meta(self, spec, ver):
        print self.api.meta(spec.name, ver, as_json=False)

    def print_readme(self, spec, ver):
        print self.api.readme(spec.name, ver)
        
    def print_details(self, spec, ver):
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

 
from pgxnclient.utils import sha1
from pgxnclient.errors import BadChecksum

class Download(CommandWithSpec):
    name = 'download'
    description = N_("download a distribution from the network")

    @classmethod
    def customize_parser(self, parser, subparsers, glb, **kwargs):
        subp = super(Download, self).customize_parser(
            parser, subparsers, glb, **kwargs)
        subp.add_argument('--target', metavar='PATH', default='.',
            help = _('Target directory and/or filename to save'))

        return subp

    def run(self):
        spec = self.get_spec()
        data = self.get_meta(spec)

        try:
            chk = data['sha1']
        except KeyError:
            raise PgxnClientException(
                "sha1 missing from the distribution meta")

        fin = self.api.download(spec.name, SemVer(data['version']))
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
from subprocess import Popen, PIPE
from pgxnclient.utils.zip import unpack

class WithUnpacking(object):
    def call_with_temp_dir(self, f, *args, **kwargs):
        dir = tempfile.mkdtemp()
        try:
            return f(dir, *args, **kwargs)
        finally:
            shutil.rmtree(dir)

    def unpack(self, zipname, destdir):
        return unpack(zipname, destdir)


class WithPgConfig(object):
    @classmethod
    def customize_parser(self, parser, subparsers, glb, **kwargs):
        subp = super(WithPgConfig, self).customize_parser(
            parser, subparsers, glb, **kwargs)

        subp.add_argument('--pg_config', metavar="PATH", default='pg_config',
            help = _("path to the pg_config executable to find the database"
                " [default: %(default)s]"))

        return subp

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


import shlex

class WithMake(WithPgConfig, WithUnpacking):
    def run_make(self, cmd, dir, env=None, sudo=None):
        """Invoke make with the selected command.

        :param cmd: the make target
        :param dir: the direcrory to run the command into
        :param env: variables to add to the make environment
        :param sudo: if set, use the provided command/arg to elevate
            privileges
        """
        cmdline = []

        if sudo:
            cmdline.extend(shlex.split(sudo))

        cmdline.extend(['make', 'PG_CONFIG=%s' % self.opts.pg_config])
        if cmd == 'installcheck':
            cmdline.append('PGUSER=postgres')

        cmdline.append(cmd)

        logger.debug(_("running: %s"), cmdline)
        p = Popen(cmdline, cwd=dir, shell=False, env=env, close_fds=True)
        p.communicate()
        if p.returncode:
            raise PgxnClientException(
                _("command returned %s") % p.returncode)


class InstallUninstall(WithMake, CommandWithSpec):

    @classmethod
    def customize_parser(self, parser, subparsers, glb, **kwargs):
        subp = super(InstallUninstall, self).customize_parser(
            parser, subparsers, glb,
            can_be_local=True, **kwargs)

        g = subp.add_mutually_exclusive_group()
        g.add_argument('--sudo', metavar="PROG", default='sudo',
            help = _("run PROG to elevate privileges when required"
                " [default: %(default)s]"))
        g.add_argument('--nosudo', dest='sudo', action='store_false',
            help = _("never elevate privileges"))

        return subp

    def run(self):
        return self.call_with_temp_dir(self._run)

    def _run(self, dir):
        spec = self.get_spec(can_be_local=True)
        if spec.is_dir():
            pdir = spec.dirname
        elif spec.is_file():
            pdir = self.unpack(spec.filename, dir)
        else:   # download
            self.opts.target = dir
            fn = Download(self.opts).run()
            pdir = self.unpack(fn, dir)

        self.maybe_run_configure(pdir)

        logger.info(_("building extension"))
        self.run_make('all', dir=pdir)

        self._inun(pdir)

    def _inun(self, pdir):
        """Run the specific command, implemented in the subclass."""
        raise NotImplementedError

    def maybe_run_configure(self, dir):
        fn = os.path.join(dir, 'configure')
        logger.debug("checking '%s'", fn)
        # TODO: probably not portable
        if not os.path.exists(fn):
            return

        logger.info(_("running configure"))
        p = Popen(fn, cwd=dir)
        p.communicate()
        if p.returncode:
            raise PgxnClientException(
                _("configure failed with return code %s") % p.returncode)

class Install(InstallUninstall):
    name = 'install'
    description = N_("download, build and install a distribution")

    def _inun(self, pdir):
        logger.info(_("installing extension"))
        self.run_make('install', dir=pdir, sudo=self.opts.sudo)

class Uninstall(InstallUninstall):
    name = 'uninstall'
    description = N_("remove a distribution from the system")

    def _inun(self, pdir):
        logger.info(_("removing extension"))
        self.run_make('uninstall', dir=pdir, sudo=self.opts.sudo)


class WithDatabase(object):
    @classmethod
    def customize_parser(self, parser, subparsers, glb, **kwargs):
        subp = super(WithDatabase, self).customize_parser(
            parser, subparsers, glb, **kwargs)

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
        if self.opts.dbname: rv.extend(['--dbname', self.opts.dbname])
        if self.opts.host: rv.extend(['--host', self.opts.host])
        if self.opts.port: rv.extend(['--port', str(self.opts.port)])
        if self.opts.username: rv.extend(['--username', self.opts.username])
        return rv

    def get_psql_env(self):
        """Return a dict with env variables to connect to the specified db."""
        rv = {}
        if self.opts.dbname: rv['PGDATABASE'] = self.opts.dbname
        if self.opts.host: rv['PGHOST'] = self.opts.host
        if self.opts.port: rv['PGPORT'] = str(self.opts.port)
        # TODO: PGUSER doesn't get passed?
        if self.opts.username: rv['PGUSER'] = self.opts.username
        return rv


class Check(WithMake, WithDatabase, CommandWithSpec):
    name = 'check'
    description = N_("run a distribution's test")

    def run(self):
        return self.call_with_temp_dir(self._run)

    def _run(self, dir):
        self.opts.target = dir
        fn = Download(self.opts).run()
        pdir = self.unpack(fn, dir)

        logger.info(_("checking extension"))
        env = os.environ.copy()
        env.update(self.get_psql_env())
        try:
            self.run_make('installcheck', dir=pdir, env=env)
        except PgxnClientException, e:
            # if the test failed, copy locally the regression result
            for ext in ('out', 'diffs'):
                fn = os.path.join(pdir, 'regression.' + ext)
                if os.path.exists(fn):
                    logger.info(_('copying regression.%s'), ext)
                    shutil.copy(fn, './regression.' + ext)
            raise


class LoadUnload(WithPgConfig, WithDatabase, CommandWithSpec):
    @classmethod
    def customize_parser(self, parser, subparsers, glb, **kwargs):
        subp = super(LoadUnload, self).customize_parser(
            parser, subparsers, glb,
            can_be_local=True, **kwargs)

        return subp

    def get_pg_version(self):
        """Return the version of the selected database."""
        data = self.call_psql('SELECT version();')
        pgver = self.parse_pg_version(data)
        logger.debug("PostgreSQL version: %d.%d.%d", *pgver)
        return pgver

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

class Load(LoadUnload):
    name = 'load'
    description = N_("load a distribution's extensions into a database")

    def run(self):
        spec = self.get_spec(can_be_local=True)
        dist = self.get_meta(spec)

        # TODO: probably unordered before Python 2.7 or something
        for name, data in dist['provides'].items():
            sql = data.get('file')
            self.load_ext(name, sql)

    def load_ext(self, name, sqlfile):
        pgver = self.get_pg_version()

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

    def create_extension(self, name):
        # TODO: namespace etc.
        cmd = "CREATE EXTENSION %s;" % Label(name)
        self.load_sql(data=cmd)

class Unload(LoadUnload):
    name = 'unload'
    description = N_("unload a distribution's extensions from a database")

    def run(self):
        spec = self.get_spec(can_be_local=True)
        dist = self.get_meta(spec)

        # TODO: ensure ordering
        provs = dist['provides'].items()
        provs.reverse()
        for name, data in provs:
            sql = data.get('file')
            self.load_ext(name, sql)

    def load_ext(self, name, sqlfile):
        pgver = self.get_pg_version()

        if pgver >= (9,1,0):
            if self.is_extension(name):
                self.drop_extension(name)
                return
            else:
                self.confirm(_("""\
The extension '%s' doesn't contain a control file:
will look for an SQL script to unload the objects.
Do you want to continue?""")
                    % name)

        if not sqlfile:
            sqlfile = name + '.sql'

        sqlfile = 'uninstall_' + sqlfile

        fn = self.find_sql_file(name, sqlfile)
        self.confirm(_("""\
In order to unload the extension '%s' looks like you will have
to load the file '%s'.
Do you want to execute it?""")
                % (name, fn))

        self.load_sql(fn)

    def drop_extension(self, name):
        # TODO: namespace etc.
        # TODO: cascade
        cmd = "DROP EXTENSION %s;" % Label(name)
        self.load_sql(data=cmd)

