"""
pgxnclient -- commands package

This module contains base classes and functions to implement and deal with
commands. Concrete commands implementations are available in other package
modules.
"""

# Copyright (C) 2011-2012 Daniele Varrazzo

# This file is part of the PGXN client

from __future__ import with_statement

import os
import sys
import logging
from subprocess import Popen, PIPE

from pgxnclient.utils import load_json, argparse, find_executable

from pgxnclient import __version__
from pgxnclient import network
from pgxnclient import Spec, SemVer
from pgxnclient import archive
from pgxnclient.api import Api
from pgxnclient.i18n import _, gettext
from pgxnclient.errors import NotFound, PgxnClientException, ProcessError, ResourceNotFound, UserAbort
from pgxnclient.utils.temp import temp_dir

logger = logging.getLogger('pgxnclient.commands')


def get_option_parser():
    """
    Return an option parser populated with the available commands.

    The parser is populated with all the options defined by the implemented
    commands.  Only commands defining a ``name`` attribute are added.
    The function relies on the `Command` subclasses being already
    created: call `load_commands()` before calling this function.
    """
    parser = argparse.ArgumentParser(
        # usage = _("%(prog)s [global options] COMMAND [command options]"),
        description =
            _("Interact with the PostgreSQL Extension Network (PGXN)."),
    )
    parser.add_argument("--version", action='version',
        version="%%(prog)s %s" % __version__,
        help = _("print the version number and exit"))

    subparsers = parser.add_subparsers(
        title = _("available commands"),
        metavar = 'COMMAND',
        help = _("the command to execute."
            " The complete list is available using `pgxn help --all`."
            " Builtin commands are:"))

    clss = [ cls for cls in CommandType.subclasses if cls.name ]
    clss.sort(key=lambda c: c.name)
    for cls in clss:
        cls.customize_parser(parser, subparsers)

    return parser

def load_commands():
    """
    Load all the commands known by the program.

    Currently commands are read from modules into the `pgxnclient.commands`
    package.

    Importing the package causes the `Command` classes to be created: they
    register themselves thanks to the `CommandType` metaclass.
    """
    pkgdir = os.path.dirname(__file__)
    for fn in os.listdir(pkgdir):
        if fn.startswith('_'): continue
        modname = __name__ + '.' + os.path.splitext(fn)[0]

        # skip already imported modules
        if modname in sys.modules: continue

        try:
            __import__(modname)
        except Exception, e:
            logger.warn(_("error importing commands module %s: %s - %s"),
                modname, e.__class__.__name__, e)


def run_command(opts, parser):
    """Run the command specified by options parsed on the command line."""
    # setup the logging
    logging.getLogger().setLevel(
        opts.verbose and logging.DEBUG or logging.INFO)
    return opts.cmd(opts, parser=parser).run()


class CommandType(type):
    """
    Metaclass for the Command class.

    This metaclass allows self-registration of the commands: any Command
    subclass is automatically added to the `subclasses` list.
    """
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

    Commands should subclass this class and possibly other mixin classes, set
    a value for the `name` and `description` arguments and implement the
    `run()` method. If command line parser customization is required,
    `customize_parser()` should be extended.
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
    def customize_parser(self, parser, subparsers, **kwargs):
        """Customise the option parser.

        :param parser: the option parser to be customized
        :param subparsers: the action object where to register a command subparser
        :return: the new subparser created

        Subclasses should extend this method in order to add new options or a
        subparser implementing a new command. Be careful in calling the
        superclass' `customize_parser()` via `super()` in order to call all
        the mixins methods. Also note that the method must be a classmethod.
        """
        return self.__make_subparser(parser, subparsers, **kwargs)

    def run(self):
        """The actions to take when the command is invoked."""
        raise NotImplementedError

    @classmethod
    def __make_subparser(self, parser, subparsers,
            description=None, epilog=None):
        """Create a new subparser with help populated."""
        subp = subparsers.add_parser(self.name,
            help = gettext(self.description),
            description = description or gettext(self.description),
            epilog = epilog)
        subp.set_defaults(cmd=self)

        glb = subp.add_argument_group(_("global options"))
        glb.add_argument("--mirror", metavar="URL",
            default = 'http://api.pgxn.org/',
            help = _("the mirror to interact with [default: %(default)s]"))
        glb.add_argument("--verbose", action='store_true',
            help = _("print more information"))
        glb.add_argument("--yes", action='store_true',
            help = _("assume affirmative answer to all questions"))

        return subp

    @property
    def api(self):
        """Return an `Api` instance to communicate with PGXN.

        Use the value provided with ``--mirror`` to decide where to connect.
        """
        if self._api is None:
            self._api = Api(mirror=self.opts.mirror)

        return self._api

    def confirm(self, prompt):
        """Prompt an user confirmation.

        Raise `UserAbort` if the user replies "no".

        The method is no-op if the ``--yes`` option is specified.
        """
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

    def popen(self, cmd, *args, **kwargs):
        """
        Excecute subprocess.Popen.

        Commands should use this method instead of importing subprocess.Popen:
        this allows replacement with a mock in the test suite.
        """
        logger.debug("running command: %s", cmd)
        try:
            return Popen(cmd, *args, **kwargs)
        except OSError, e:
            if not isinstance(cmd, basestring):
                cmd = ' '.join(cmd)
            msg = _("%s running command: %s") % (e, cmd)
            raise ProcessError(msg)


from pgxnclient.errors import BadSpecError

class WithSpec(Command):
    """Mixin to implement commands taking a package specification.

    This class adds a positional argument SPEC to the parser and related
    options.
    """
    @classmethod
    def customize_parser(self, parser, subparsers,
        with_status=True, epilog=None, **kwargs):
        """
        Add the SPEC related options to the parser.

        If *with_status* is true, options ``--stable``, ``--testing``,
        ``--unstable`` are also handled.
        """
        epilog = _("""
SPEC can either specify just a name or contain required versions
indications, for instance 'pkgname=1.0', or 'pkgname>=2.1'.
""") + (epilog or "")

        subp = super(WithSpec, self).customize_parser(
            parser, subparsers, epilog=epilog, **kwargs)

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

    def get_spec(self, _can_be_local=False, _can_be_url=False):
        """
        Return the package specification requested.

        Return a `Spec` instance.
        """
        spec = self.opts.spec

        try:
            spec = Spec.parse(spec)
        except (ValueError, BadSpecError), e:
            self.parser.error(_("cannot parse package '%s': %s")
                % (spec, e))

        if not _can_be_local and spec.is_local():
            raise PgxnClientException(
                _("you cannot use a local resource with this command"))

        if not _can_be_url and spec.is_url():
            raise PgxnClientException(
                _("you cannot use an url with this command"))

        return spec

    def get_best_version(self, data, spec, quiet=False):
        """
        Return the best version an user may want for a distribution.

        Return a `SemVer` instance.

        Raise `ResourceNotFound` if no version is found with the provided
        specification and options.
        """
        drels = data['releases']

        # Get the maximum version for each release status satisfying the spec
        vers = [ None ] * len(Spec.STATUS)
        for n, d in drels.iteritems():
            vs = filter(spec.accepted, [SemVer(r['version']) for r in d])
            if vs:
                vers[Spec.STATUS[n]] = max(vs)

        return self._get_best_version(vers, spec, quiet)

    def get_best_version_from_ext(self, data, spec):
        """
        Return the best distribution version from an extension's data
        """
        # Get the maximum version for each release status satisfying the spec
        vers = [ [] for i in xrange(len(Spec.STATUS)) ]
        vmap = {} # ext_version -> (dist_name, dist_version)
        for ev, dists in data.get('versions', {}).iteritems():
            ev = SemVer(ev)
            if not spec.accepted(ev):
                continue
            for dist in dists:
                dv = SemVer(dist['version'])
                ds = dist.get('status', 'stable')
                vers[Spec.STATUS[ds]].append(ev)
                vmap[ev] = (dist['dist'], dv)

        # for each rel status only take the max one.
        for i in xrange(len(vers)):
            vers[i] = vers[i] and max(vers[i]) or None

        ev = self._get_best_version(vers, spec, quiet=False)
        return vmap[ev]

    def _get_best_version(self, vers, spec, quiet):
        # Is there any result at the desired release status?
        want = [ v for lvl, v in enumerate(vers)
            if lvl >= self.opts.status and v is not None ]
        if want:
            ver = max(want)
            if not quiet:
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
        """
        Return the content of the ``META.json`` file for *spec*.

        Return the object obtained parsing the JSON.
        """
        if spec.is_name():
            # Get the metadata from the API
            try:
                data = self.api.dist(spec.name)
            except NotFound:
                # Distro not found: maybe it's an extension?
                ext = self.api.ext(spec.name)
                name, ver = self.get_best_version_from_ext(ext, spec)
                return self.api.meta(name, ver)
            else:
                ver = self.get_best_version(data, spec)
                return self.api.meta(spec.name, ver)

        elif spec.is_dir():
            # Get the metadata from a directory
            fn = os.path.join(spec.dirname, 'META.json')
            logger.debug("reading %s", fn)
            if not os.path.exists(fn):
                raise PgxnClientException(
                    _("file 'META.json' not found in '%s'") % dir)

            with open(fn) as f:
                return load_json(f)

        elif spec.is_file():
            arc = archive.from_spec(spec)
            return arc.get_meta()

        elif spec.is_url():
            with network.get_file(spec.url) as fin:
                with temp_dir() as dir:
                    fn = network.download(fin, dir)
                    arc = archive.from_file(fn)
                    return arc.get_meta()

        else:
            assert False

class WithSpecLocal(WithSpec):
    """
    Mixin to implement commands that can also refer to a local file or dir.
    """

    @classmethod
    def customize_parser(self, parser, subparsers, epilog=None, **kwargs):
        epilog = _("""
SPEC may also be a local zip file or unpacked directory, but in this case
it should contain at least a '%s', for instance '.%spkgname.zip'.
""") % (os.sep, os.sep) + (epilog or "")

        subp = super(WithSpecLocal, self).customize_parser(
            parser, subparsers, epilog=epilog, **kwargs)

        return subp

    def get_spec(self, **kwargs):
        kwargs['_can_be_local'] = True
        return super(WithSpecLocal, self).get_spec(**kwargs)


class WithSpecUrl(WithSpec):
    """
    Mixin to implement commands that can also refer to a URL.
    """

    @classmethod
    def customize_parser(self, parser, subparsers, epilog=None, **kwargs):
        epilog = _("""
SPEC may also be an url specifying a protocol such as 'http://' or 'https://'.
""") + (epilog or "")

        subp = super(WithSpecUrl, self).customize_parser(
            parser, subparsers, epilog=epilog, **kwargs)

        return subp

    def get_spec(self, **kwargs):
        kwargs['_can_be_url'] = True
        return super(WithSpecUrl, self).get_spec(**kwargs)


class WithPgConfig(object):
    """
    Mixin to implement commands that should query :program:`pg_config`.
    """
    @classmethod
    def customize_parser(self, parser, subparsers, **kwargs):
        """
        Add the ``--pg_config`` option to the options parser.
        """
        subp = super(WithPgConfig, self).customize_parser(
            parser, subparsers, **kwargs)

        subp.add_argument('--pg_config', metavar="PROG", default='pg_config',
            help = _("the pg_config executable to find the database"
                " [default: %(default)s]"))

        return subp

    def call_pg_config(self, what, _cache={}):
        """
        Call :program:`pg_config` and return its output.
        """
        if what in _cache:
            return _cache[what]

        logger.debug("running pg_config --%s", what)
        cmdline = [self.get_pg_config(), "--%s" % what]
        p = self.popen(cmdline, stdout=PIPE)
        out, err = p.communicate()
        if p.returncode:
            raise ProcessError(_("command returned %s: %s")
                % (p.returncode, cmdline))

        out = out.rstrip().decode('utf-8')
        rv = _cache[what] = out
        return rv

    def get_pg_config(self):
        """
        Return the absolute path of the pg_config binary.
        """
        pg_config = self.opts.pg_config
        if os.path.split(pg_config)[0]:
            pg_config = os.path.abspath(pg_config)
        else:
            pg_config = find_executable(pg_config)
        if not pg_config:
            raise PgxnClientException(_("pg_config executable not found"))
        return pg_config


import shlex

class WithMake(WithPgConfig):
    """
    Mixin to implement commands that should invoke :program:`make`.
    """
    @classmethod
    def customize_parser(self, parser, subparsers, **kwargs):
        """
        Add the ``--make`` option to the options parser.
        """
        subp = super(WithMake, self).customize_parser(
            parser, subparsers, **kwargs)

        subp.add_argument('--make', metavar="PROG",
            default=self._find_default_make(),
            help = _("the 'make' executable to use to build the extension "
                "[default: %(default)s]"))

        return subp

    def run_make(self, cmd, dir, env=None, sudo=None):
        """Invoke make with the selected command.

        :param cmd: the make target or list of options to pass make
        :param dir: the direcrory to run the command into
        :param env: variables to add to the make environment
        :param sudo: if set, use the provided command/arg to elevate
            privileges
        """
        # check if the directory contains a makefile
        for fn in ('GNUmakefile', 'makefile', 'Makefile'):
            if os.path.exists(os.path.join(dir, fn)):
                break
        else:
            raise PgxnClientException(
                _("no Makefile found in the extension root"))

        cmdline = []

        if sudo:
            cmdline.extend(shlex.split(sudo))

        cmdline.extend([self.get_make(), 'PG_CONFIG=%s' % self.get_pg_config()])

        if isinstance(cmd, basestring):
            cmdline.append(cmd)
        else: # a list
            cmdline.extend(cmd)

        logger.debug(_("running: %s"), cmdline)
        p = self.popen(cmdline, cwd=dir, shell=False, env=env, close_fds=True)
        p.communicate()
        if p.returncode:
            raise ProcessError(_("command returned %s: %s")
                % (p.returncode, ' '.join(cmdline)))

    def get_make(self, _cache=[]):
        """
        Return the path of the make binary.
        """
        # the cache is not for performance but to return a consistent value
        # even if the cwd is changed
        if _cache:
            return _cache[0]

        make = self.opts.make

        if os.path.split(make)[0]:
            # At least a relative dir specified.
            if not os.path.exists(make):
                raise PgxnClientException(_("make executable not found: %s")
                    % make)

            # Convert to abs path to be robust in case the dir is changed.
            make = os.path.abspath(make)

        else:
            # we don't find make here and convert to abs path because it's a
            # security hole: make may be run under sudo and in this case we
            # don't want root to execute a make hacked in an user local dir
            if not find_executable(make):
                raise PgxnClientException(_("make executable not found: %s")
                    % make)

        _cache.append(make)
        return make

    @classmethod
    def _find_default_make(self):
        for make in ('gmake', 'make'):
            path = find_executable(make)
            if path:
                return make

        # if nothing was found, fall back on 'gmake'. If it was missing we
        # will give an error when attempting to use it
        return 'gmake'


class WithSudo(object):
    """
    Mixin to implement commands that may invoke sudo.
    """
    @classmethod
    def customize_parser(self, parser, subparsers, **kwargs):
        subp = super(WithSudo, self).customize_parser(
            parser, subparsers, **kwargs)

        g = subp.add_mutually_exclusive_group()
        g.add_argument('--sudo', metavar="PROG", const='sudo', nargs="?",
            help = _("run PROG to elevate privileges when required"
                " [default: %(const)s]"))
        g.add_argument('--nosudo', dest='sudo', action='store_false',
            help = _("never elevate privileges "
                "(no more needed: for backward compatibility)"))

        return subp


class WithDatabase(object):
    """
    Mixin to implement commands that should communicate to a database.
    """
    @classmethod
    def customize_parser(self, parser, subparsers, epilog=None, **kwargs):
        """
        Add the options related to database connections.
        """
        epilog =  _("""
The default database connection options depend on the value of environment
variables PGDATABASE, PGHOST, PGPORT, PGUSER.
""") + (epilog or "")

        subp = super(WithDatabase, self).customize_parser(
            parser, subparsers, epilog=epilog, **kwargs)

        g = subp.add_argument_group(_("database connections options"))

        g.add_argument('-d', '--dbname', metavar="DBNAME",
            help = _("database name to install into"))
        g.add_argument('-h', '--host', metavar="HOST",
            help = _("database server host or socket directory"))
        g.add_argument('-p', '--port', metavar="PORT", type=int,
            help = _("database server port"))
        g.add_argument('-U', '--username', metavar="NAME",
            help = _("database user name"))

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
        """
        Return a dict with env variables to connect to the specified db.
        """
        rv = {}
        if self.opts.dbname: rv['PGDATABASE'] = self.opts.dbname
        if self.opts.host: rv['PGHOST'] = self.opts.host
        if self.opts.port: rv['PGPORT'] = str(self.opts.port)
        if self.opts.username: rv['PGUSER'] = self.opts.username
        return rv

