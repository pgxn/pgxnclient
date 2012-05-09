"""
pgxnclient -- installation/loading commands implementation
"""

# Copyright (C) 2011 Daniele Varrazzo

# This file is part of the PGXN client

import os
import re
import sys
import shutil
import difflib
import logging
from subprocess import PIPE

from pgxnclient import SemVer
from pgxnclient.i18n import _, N_
from pgxnclient.utils import sha1
from pgxnclient.errors import BadChecksum, PgxnClientException
from pgxnclient.network import download
from pgxnclient.commands import Command, WithDatabase, WithMake, WithPgConfig
from pgxnclient.commands import WithSpec, WithSpecLocal, WithSudo
from pgxnclient.utils.strings import Identifier

logger = logging.getLogger('pgxnclient.commands')


class Download(WithSpec, Command):
    name = 'download'
    description = N_("download a distribution from the network")

    @classmethod
    def customize_parser(self, parser, subparsers, **kwargs):
        subp = super(Download, self).customize_parser(
            parser, subparsers, **kwargs)
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

        fin = self.api.download(data['name'], SemVer(data['version']))
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


class InstallUninstall(WithMake, WithSpecLocal, Command):
    """
    Base class to implement the ``install`` and ``uninstall`` commands.
    """
    def run(self):
        return self.call_with_temp_dir(self._run)

    def _run(self, dir):
        spec = self.get_spec()
        if spec.is_dir():
            pdir = os.path.abspath(spec.dirname)
        elif spec.is_file():
            pdir = self.unpack(spec.filename, dir)
        else:   # download
            self.opts.target = dir
            fn = Download(self.opts).run()
            pdir = self.unpack(fn, dir)

        self.maybe_run_configure(pdir)

        self._inun(pdir)

    def _inun(self, pdir):
        """Run the specific command, implemented in the subclass."""
        raise NotImplementedError

    def maybe_run_configure(self, dir):
        fn = os.path.join(dir, 'configure')
        logger.debug("checking '%s'", fn)
        if not os.path.exists(fn):
            return

        logger.info(_("running configure"))
        p = self.popen(fn, cwd=dir)
        p.communicate()
        if p.returncode:
            raise PgxnClientException(
                _("configure failed with return code %s") % p.returncode)


class Install(WithSudo, InstallUninstall):
    name = 'install'
    description = N_("download, build and install a distribution")

    def _inun(self, pdir):
        logger.info(_("building extension"))
        self.run_make('all', dir=pdir)

        logger.info(_("installing extension"))
        self.run_make('install', dir=pdir, sudo=self.opts.sudo)


class Uninstall(WithSudo, InstallUninstall):
    name = 'uninstall'
    description = N_("remove a distribution from the system")

    def _inun(self, pdir):
        logger.info(_("removing extension"))
        self.run_make('uninstall', dir=pdir, sudo=self.opts.sudo)


class Check(WithDatabase, InstallUninstall):
    name = 'check'
    description = N_("run a distribution's test")

    def _inun(self, pdir):
        logger.info(_("checking extension"))
        upenv = self.get_psql_env()
        logger.debug("additional env: %s", upenv)
        env = os.environ.copy()
        env.update(upenv)

        cmd = ['installcheck']
        if 'PGDATABASE' in upenv:
            cmd.append("CONTRIB_TESTDB=" +  env['PGDATABASE'])

        try:
            self.run_make(cmd, dir=pdir, env=env)
        except PgxnClientException:
            # if the test failed, copy locally the regression result
            for ext in ('out', 'diffs'):
                fn = os.path.join(pdir, 'regression.' + ext)
                if os.path.exists(fn):
                    dest = './regression.' + ext
                    if not os.path.exists(dest) or not os.path.samefile(fn, dest):
                        logger.info(_('copying regression.%s'), ext)
                        shutil.copy(fn, dest)
            raise


class LoadUnload(WithPgConfig, WithDatabase, WithSpecLocal, Command):
    """
    Base class to implement the ``load`` and ``unload`` commands.
    """
    @classmethod
    def customize_parser(self, parser, subparsers, **kwargs):
        subp = super(LoadUnload, self).customize_parser(
            parser, subparsers, **kwargs)

        subp.add_argument('--schema', metavar="SCHEMA",
            type=Identifier.parse_arg,
            help=_("use SCHEMA instead of the default schema"))

        subp.add_argument('extensions', metavar='EXT', nargs='*',
            help = _("only specified extensions [default: all]"))

        return subp

    def get_pg_version(self):
        """Return the version of the selected database."""
        data = self.call_psql('SELECT version();')
        pgver = self.parse_pg_version(data)
        logger.debug("PostgreSQL version: %d.%d.%d", *pgver)
        return pgver

    def parse_pg_version(self, data):
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
        p = self.popen(cmdline, stdout=PIPE)
        out, err = p.communicate()
        if p.returncode:
            raise PgxnClientException(
                "psql returned %s running command" % (p.returncode))

        return out.decode('utf-8')

    def load_sql(self, filename=None, data=None):
        cmdline = [self.find_psql()]
        cmdline.extend(self.get_psql_options())
        # load via pipe to enable psql commands in the file
        if not data:
            fin = open(filename, 'r')
            p = self.popen(cmdline, stdin=fin)
            p.communicate()
        else:
            p = self.popen(cmdline, stdin=PIPE)
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

    def patch_for_schema(self, fn):
        """
        Patch a sql file to set the schema where the commands are executed.

        If no schema has been requested, return the data unchanged.
        Else, ask for confirmation and return the data for a patched file.

        The schema is only useful for PG < 9.1: for proper PG extensions there
        is no need to patch the sql.
        """
        schema = self.opts.schema

        f = open(fn)
        try: data = f.read()
        finally: f.close()

        if not schema:
            return data

        self._check_schema_exists(schema)

        re_path = re.compile(r'SET\s+search_path\s*(?:=|to)\s*([^;]+);', re.I)
        m = re_path.search(data)
        if m is None:
            newdata = ("SET search_path = %s;\n\n" % schema) + data
        else:
            newdata = re_path.sub("SET search_path = %s;" % schema, data)

        diff = ''.join(difflib.unified_diff(
            [r + '\n' for r in data.splitlines()],
            [r + '\n' for r in newdata.splitlines()],
            fn, fn + ".schema"))
        msg = _("""
In order to operate in the schema %s, the following changes will be
performed:\n\n%s\n\nDo you want to continue?""")
        self.confirm(msg % (schema, diff))

        return newdata

    def _register_loaded(self, fn):
        if not hasattr(self, '_loaded'):
            self._loaded = []

        self._loaded.append(fn)

    def _is_loaded(self, fn):
        return hasattr(self, '_loaded') and fn in self._loaded

    def _check_schema_exists(self, schema):
        cmdline = [self.find_psql()]
        cmdline.extend(self.get_psql_options())
        cmdline.extend(['-c', 'SET search_path=%s' % schema])
        p = self.popen(cmdline, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        p.communicate()
        if p.returncode:
            raise PgxnClientException(
                "schema %s does not exist" % schema)

    def _get_extensions(self):
        """
        Return a list of pairs (name, sql file) to be loaded/unloaded.

        Items are in loading order.
        """
        spec = self.get_spec()
        dist = self.get_meta(spec)

        if 'provides' not in dist:
            # No 'provides' specified: assume a single extension named
            # after the distribution. This is automatically done by PGXN,
            # but we should do ourselves to deal with local META files
            # not mangled by the PGXN upload script yet.
            name = dist['name']
            for ext in self.opts.extensions:
                if ext <> name:
                    raise PgxnClientException(
                        "can't find extension '%s' in the distribution '%s'"
                            % (name, spec))

            return [ (name, None) ]

        rv = []

        if not self.opts.extensions:
            # All the extensions, in the order specified
            if len(dist['provides']) > 1 and sys.version_info < (2, 5):
                logger.warn(_("can't guarantee extensions load order "
                    "with Python < 2.5"))
            for name, data in dist['provides'].items():
                rv.append((name, data.get('file')))
        else:
            # Only the specified extensions
            for name in self.opts.extensions:
                try:
                    data = dist['provides'][name]
                except KeyError:
                    raise PgxnClientException(
                        "can't find extension '%s' in the distribution '%s'"
                            % (name, spec))
                rv.append((name, data.get('file')))

        return rv


class Load(LoadUnload):
    name = 'load'
    description = N_("load a distribution's extensions into a database")

    def run(self):
        items = self._get_extensions()
        for (name, sql) in items:
            self.load_ext(name, sql)

    def load_ext(self, name, sqlfile):
        logger.debug(_("loading extension '%s' with file: %s"),
            name, sqlfile)

        if sqlfile and not sqlfile.endswith('.sql'):
            logger.info(
                _("the specified file '%s' doesn't seem SQL:"
                    " assuming '%s' is not a PostgreSQL extension"),
                    sqlfile, name)
            return

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

        # TODO: is confirmation asked only once? Also, check for repetition
        # in unload.
        if self._is_loaded(fn):
            logger.info(_("file %s already loaded"), fn)
        else:
            data = self.patch_for_schema(fn)
            self.load_sql(data=data)
            self._register_loaded(fn)

    def create_extension(self, name):
        name = Identifier(name)
        schema = self.opts.schema
        cmd = ["CREATE EXTENSION", name]
        if schema:
            cmd.extend(["SCHEMA", schema])

        cmd = " ".join(cmd) + ';'
        self.load_sql(data=cmd)


class Unload(LoadUnload):
    name = 'unload'
    description = N_("unload a distribution's extensions from a database")

    def run(self):
        items = self._get_extensions()

        if not self.opts.extensions:
            items.reverse()

        for (name, sql) in items:
            self.unload_ext(name, sql)

    def unload_ext(self, name, sqlfile):
        logger.debug(_("unloading extension '%s' with file: %s"),
            name, sqlfile)

        if sqlfile and not sqlfile.endswith('.sql'):
            logger.info(
                _("the specified file '%s' doesn't seem SQL:"
                    " assuming '%s' is not a PostgreSQL extension"),
                    sqlfile, name)
            return

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

        tmp = os.path.split(sqlfile)
        sqlfile = os.path.join(tmp[0], 'uninstall_' + tmp[1])

        fn = self.find_sql_file(name, sqlfile)
        self.confirm(_("""\
In order to unload the extension '%s' looks like you will have
to load the file '%s'.
Do you want to execute it?""")
                % (name, fn))

        data = self.patch_for_schema(fn)
        self.load_sql(data=data)

    def drop_extension(self, name):
        # TODO: cascade
        cmd = "DROP EXTENSION %s;" % Identifier(name)
        self.load_sql(data=cmd)

