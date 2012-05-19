"""
pgxnclient -- commands package

This module contains base classes and functions to implement and deal with
commands. Concrete commands implementations are available in other package
modules.
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

import os
import sys
import logging
from subprocess import Popen, PIPE

from pgxnclient.utils import load_json
from pgxnclient.utils import argparse

from pgxnclient import __version__
from pgxnclient import Spec, SemVer
from pgxnclient.api import Api
from pgxnclient.i18n import _, gettext
from pgxnclient.errors import NotFound, PgxnClientException, ProcessError, ResourceNotFound, UserAbort

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
from pgxnclient.utils.zip import get_meta_from_zip

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

    def get_spec(self, _can_be_local=False):
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
        if not spec.is_local():
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

            return load_json(open(fn))

        elif spec.is_file():
            # Get the metadata from a zip file
            return get_meta_from_zip(spec.filename)


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

    def get_spec(self):
        return super(WithSpecLocal, self).get_spec(_can_be_local=True)


import shutil
import tempfile
from pgxnclient.utils.zip import unpack

class WithUnpacking(object):
    """
    Mixin to implement commands that may deal with zip files.
    """
    def call_with_temp_dir(self, f, *args, **kwargs):
        """
        Call a function in the context of a temporary directory.

        Create the temp directory and pass its name as first argument to *f*.
        Other arguments and keywords are passed to *f* too. Upon exit delete
        the directory.
        """
        dir = tempfile.mkdtemp()
        try:
            return f(dir, *args, **kwargs)
        finally:
            shutil.rmtree(dir)

    def unpack(self, zipname, destdir):
        """Unpack the zip file *zipname* into *destdir*."""
        return unpack(zipname, destdir)


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

        subp.add_argument('--pg_config', metavar="PATH", default='pg_config',
            help = _("path to the pg_config executable to find the database"
                " [default: %(default)s]"))

        return subp

    def call_pg_config(self, what, _cache={}):
        """
        Call :program:`pg_config` and return its output.
        """
        if what in _cache:
            return _cache[what]

        logger.debug("running pg_config --%s", what)
        cmdline = [self.opts.pg_config, "--%s" % what]
        p = self.popen(cmdline, stdout=PIPE)
        out, err = p.communicate()
        if p.returncode:
            raise ProcessError(_("command returned %s: %s")
                % (p.returncode, cmdline))

        out = out.rstrip().decode('utf-8')
        rv = _cache[what] = out
        return rv


import shlex

class WithMake(WithPgConfig, WithUnpacking):
    """
    Mixin to implement commands that should invoke :program:`make`.
    """
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

        # convert to absolute path for makefile, or else it may miss it
        # if the cwd is changed during execution
        pg_config = self.opts.pg_config
        if os.path.split(pg_config)[0]:
            pg_config = os.path.abspath(pg_config)

        cmdline.extend(['make', 'PG_CONFIG=%s' % pg_config])

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


class WithSudo(object):
    """
    Mixin to implement commands that may invoke sudo.
    """
    @classmethod
    def customize_parser(self, parser, subparsers, **kwargs):
        subp = super(WithSudo, self).customize_parser(
            parser, subparsers, **kwargs)

        g = subp.add_mutually_exclusive_group()
        g.add_argument('--sudo', metavar="PROG", default='sudo',
            help = _("run PROG to elevate privileges when required"
                " [default: %(default)s]"))
        g.add_argument('--nosudo', dest='sudo', action='store_false',
            help = _("never elevate privileges"))

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

