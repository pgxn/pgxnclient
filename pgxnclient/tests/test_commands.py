from mock import patch, Mock

import os
import tempfile
import shutil
from urllib import quote

from pgxnclient.utils import b
from pgxnclient.errors import PgxnClientException, ResourceNotFound, InsufficientPrivileges
from pgxnclient.tests import unittest
from pgxnclient.tests.testutils import ifunlink, get_test_filename

class FakeFile(object):
    def __init__(self, *args):
        self._f = open(*args)
        self.url = None

    def __enter__(self):
        self._f.__enter__()
        return self

    def __exit__(self, type, value, traceback):
        self._f.__exit__(type, value, traceback)

    def __getattr__(self, attr):
        return getattr(self._f, attr)

def fake_get_file(url, urlmap=None):
    if urlmap: url = urlmap.get(url, url)
    fn = get_test_filename(quote(url, safe=""))
    if not os.path.exists(fn):
        raise ResourceNotFound(fn)
    f = FakeFile(fn, 'rb')
    f.url = url
    return f

def fake_pg_config(**map):
    def f(what):
        return map[what]

    return f


class InfoTestCase(unittest.TestCase):
    def _get_output(self, cmdline):
        @patch('sys.stdout')
        @patch('pgxnclient.network.get_file')
        def do(mock, stdout):
            mock.side_effect = fake_get_file
            from pgxnclient.cli import main
            main(cmdline)
            return u''.join([a[0] for a, k in stdout.write.call_args_list]) \
                .encode('ascii')

        return do()

    def test_info(self):
        output = self._get_output(['info', '--versions', 'foobar'])
        self.assertEqual(output, b("""\
foobar 0.43.2b1 testing
foobar 0.42.1 stable
foobar 0.42.0 stable
"""))

    def test_info_op(self):
        output = self._get_output(['info', '--versions', 'foobar>0.42.0'])
        self.assertEqual(output, b("""\
foobar 0.43.2b1 testing
foobar 0.42.1 stable
"""))

    def test_info_empty(self):
        output = self._get_output(['info', '--versions', 'foobar>=0.43.2'])
        self.assertEqual(output, b(""))

    def test_info_case_insensitive(self):
        output = self._get_output(['info', '--versions', 'Foobar'])
        self.assertEqual(output, b("""\
foobar 0.43.2b1 testing
foobar 0.42.1 stable
foobar 0.42.0 stable
"""))

    def test_mirrors_list(self):
        output = self._get_output(['mirror'])
        self.assertEqual(output, b("""\
http://pgxn.depesz.com/
http://www.postgres-support.ch/pgxn/
http://pgxn.justatheory.com/
http://pgxn.darkixion.com/
http://mirrors.cat.pdx.edu/pgxn/
http://pgxn.dalibo.org/
http://pgxn.cxsoftware.org/
http://api.pgxn.org/
"""))

    def test_mirror_info(self):
        output = self._get_output(['mirror', 'http://pgxn.justatheory.com/'])
        self.assertEqual(output, b("""\
uri: http://pgxn.justatheory.com/
frequency: daily
location: Portland, OR, USA
bandwidth: Cable
organization: David E. Wheeler
email: justatheory.com|pgxn
timezone: America/Los_Angeles
src: rsync://master.pgxn.org/pgxn/
rsync: 
notes: 

"""))


class CommandTestCase(unittest.TestCase):
    def test_popen_raises(self):
        from pgxnclient.commands import Command
        c = Command([])
        self.assertRaises(PgxnClientException,
            c.popen, "this-script-doesnt-exist")


class DownloadTestCase(unittest.TestCase):
    @patch('pgxnclient.network.get_file')
    def test_download_latest(self, mock):
        mock.side_effect = fake_get_file

        fn = 'foobar-0.42.1.zip'
        self.assert_(not os.path.exists(fn))

        from pgxnclient.cli import main
        try:
            main(['download', 'foobar'])
            self.assert_(os.path.exists(fn))
        finally:
            ifunlink(fn)

    @patch('pgxnclient.network.get_file')
    def test_download_testing(self, mock):
        mock.side_effect = fake_get_file

        fn = 'foobar-0.43.2b1.zip'
        self.assert_(not os.path.exists(fn))

        from pgxnclient.cli import main
        try:
            main(['download', '--testing', 'foobar'])
            self.assert_(os.path.exists(fn))
        finally:
            ifunlink(fn)

    @patch('pgxnclient.network.get_file')
    def test_download_url(self, mock):
        mock.side_effect = fake_get_file

        fn = 'foobar-0.43.2b1.zip'
        self.assert_(not os.path.exists(fn))

        from pgxnclient.cli import main
        try:
            main(['download', 'http://api.pgxn.org/dist/foobar/0.43.2b1/foobar-0.43.2b1.zip'])
            self.assert_(os.path.exists(fn))
        finally:
            ifunlink(fn)

    @patch('pgxnclient.network.get_file')
    def test_download_ext(self, mock):
        mock.side_effect = fake_get_file

        fn = 'pg_amqp-0.3.0.zip'
        self.assert_(not os.path.exists(fn))

        from pgxnclient.cli import main
        try:
            main(['download', 'amqp'])
            self.assert_(os.path.exists(fn))
        finally:
            ifunlink(fn)

    @patch('pgxnclient.network.get_file')
    def test_download_rename(self, mock):
        mock.side_effect = fake_get_file

        fn = 'foobar-0.42.1.zip'
        fn1= 'foobar-0.42.1-1.zip'
        fn2= 'foobar-0.42.1-2.zip'

        for tmp in (fn, fn1, fn2):
            self.assert_(not os.path.exists(tmp))

        try:
            f = open(fn, "w")
            f.write('test')
            f.close()

            from pgxnclient.cli import main
            main(['download', 'foobar'])
            self.assert_(os.path.exists(fn1))
            self.assert_(not os.path.exists(fn2))

            main(['download', 'foobar'])
            self.assert_(os.path.exists(fn2))

            f = open(fn)
            self.assertEquals(f.read(), 'test')
            f.close()

        finally:
            ifunlink(fn)
            ifunlink(fn1)
            ifunlink(fn2)

    @patch('pgxnclient.network.get_file')
    def test_download_bad_sha1(self, mock):
        def fakefake(url):
            return fake_get_file(url, urlmap = {
                'http://api.pgxn.org/dist/foobar/0.42.1/META.json':
                'http://api.pgxn.org/dist/foobar/0.42.1/META-badsha1.json'})

        mock.side_effect = fakefake

        fn = 'foobar-0.42.1.zip'
        self.assert_(not os.path.exists(fn))

        try:
            from pgxnclient.cli import main
            from pgxnclient.errors import BadChecksum
            e = self.assertRaises(BadChecksum,
                main, ['download', 'foobar'])

            self.assert_(not os.path.exists(fn))

        finally:
            ifunlink(fn)

    @patch('pgxnclient.network.get_file')
    def test_download_case_insensitive(self, mock):
        mock.side_effect = fake_get_file

        fn = 'pyrseas-0.4.1.zip'
        self.assert_(not os.path.exists(fn))

        from pgxnclient.cli import main
        try:
            main(['download', 'pyrseas'])
            self.assert_(os.path.exists(fn))
        finally:
            ifunlink(fn)

        try:
            main(['download', 'Pyrseas'])
            self.assert_(os.path.exists(fn))
        finally:
            ifunlink(fn)

    def test_version(self):
        from pgxnclient import Spec
        from pgxnclient.commands.install import Download
        from pgxnclient.errors import ResourceNotFound

        opt = Mock()
        opt.status = Spec.STABLE
        cmd = Download(opt)

        for spec, res, data in [
            ('foo', '1.2.0', {'stable': [ '1.2.0' ]}),
            ('foo', '1.2.0', {'stable': [ '1.2.0', '1.2.0b' ]}),
            ('foo=1.2', '1.2.0', {'stable': [ '1.2.0' ]}),
            ('foo>=1.1', '1.2.0', {'stable': [ '1.1.0', '1.2.0' ]}),
            ('foo>=1.1', '1.2.0', {
                'stable': [ '1.1.0', '1.2.0' ],
                'testing': [ '1.3.0' ],
                'unstable': [ '1.4.0' ], }),
            ]:
            spec = Spec.parse(spec)
            data = { 'releases':
                dict([(k, [{'version': v} for v in vs])
                    for k, vs in data.items()]) }

            self.assertEqual(res, cmd.get_best_version(data, spec))

        for spec, res, data in [
            ('foo>=1.3', '1.2.0', {'stable': [ '1.2.0' ]}),
            ('foo>=1.3', '1.2.0', {
                'stable': [ '1.2.0' ],
                'testing': [ '1.3.0' ], }),
            ]:
            spec = Spec.parse(spec)
            data = { 'releases':
                dict([(k, [{'version': v} for v in vs])
                    for k, vs in data.items()]) }

            self.assertRaises(ResourceNotFound, cmd.get_best_version, data, spec)

        opt.status = Spec.TESTING

        for spec, res, data in [
            ('foo>=1.1', '1.3.0', {
                'stable': [ '1.1.0', '1.2.0' ],
                'testing': [ '1.3.0' ],
                'unstable': [ '1.4.0' ], }),
            ]:
            spec = Spec.parse(spec)
            data = { 'releases':
                dict([(k, [{'version': v} for v in vs])
                    for k, vs in data.items()]) }

            self.assertEqual(res, cmd.get_best_version(data, spec))

        opt.status = Spec.UNSTABLE

        for spec, res, data in [
            ('foo>=1.1', '1.4.0', {
                'stable': [ '1.1.0', '1.2.0' ],
                'testing': [ '1.3.0' ],
                'unstable': [ '1.4.0' ], }),
            ]:
            spec = Spec.parse(spec)
            data = { 'releases':
                dict([(k, [{'version': v} for v in vs])
                    for k, vs in data.items()]) }

            self.assertEqual(res, cmd.get_best_version(data, spec))

class Assertions(object):

    make = object()

    def assertCallArgs(self, pattern, args):
        if len(pattern) != len(args):
            self.fail('args and pattern have different lengths')
        for p, a in zip(pattern, args):
            if p is self.make:
                if not a.endswith('make'):
                    self.fail('%s is not a make in %s' % (a, args))
            else:
                if not a == p:
                    self.fail('%s is not a %s in %s' % (a, p, args))

# With mock patching a method seems tricky: looks there's no way to get to
# 'self' as the mock method is unbound.
from pgxnclient.tar import TarArchive
TarArchive.unpack_orig = TarArchive.unpack

from pgxnclient.zip import ZipArchive
ZipArchive.unpack_orig = ZipArchive.unpack

class InstallTestCase(unittest.TestCase, Assertions):

    def setUp(self):
        self._p1 = patch('pgxnclient.network.get_file')
        self.mock_get = self._p1.start()
        self.mock_get.side_effect = fake_get_file

        self._p2 = patch('pgxnclient.commands.Popen')
        self.mock_popen = self._p2.start()
        self.mock_popen.return_value.returncode = 0

        self._p3 = patch('pgxnclient.commands.WithPgConfig.call_pg_config')
        self.mock_pgconfig = self._p3.start()
        self.mock_pgconfig.side_effect = fake_pg_config(
            libdir='/', bindir='/')

    def tearDown(self):
        self._p1.stop()
        self._p2.stop()
        self._p3.stop()

    def test_install_latest(self):
        from pgxnclient.cli import main
        main(['install', '--sudo', '--', 'foobar'])

        self.assertEquals(self.mock_popen.call_count, 2)
        self.assertCallArgs([self.make], self.mock_popen.call_args_list[0][0][0][:1])
        self.assertCallArgs(['sudo', self.make], self.mock_popen.call_args_list[1][0][0][:2])

    def test_install_missing_sudo(self):
        from pgxnclient.cli import main
        self.assertRaises(InsufficientPrivileges, main, ['install', 'foobar'])

    def test_install_local(self):
        self.mock_pgconfig.side_effect = fake_pg_config(
            libdir=os.environ['HOME'], bindir='/')

        from pgxnclient.cli import main
        main(['install', 'foobar'])

        self.assertEquals(self.mock_popen.call_count, 2)
        self.assertCallArgs([self.make], self.mock_popen.call_args_list[0][0][0][:1])
        self.assertCallArgs([self.make], self.mock_popen.call_args_list[1][0][0][:1])

    def test_install_url(self):
        self.mock_pgconfig.side_effect = fake_pg_config(
            libdir=os.environ['HOME'], bindir='/')

        from pgxnclient.cli import main
        main(['install', 'http://api.pgxn.org/dist/foobar/0.42.1/foobar-0.42.1.zip'])

        self.assertEquals(self.mock_popen.call_count, 2)
        self.assertCallArgs([self.make], self.mock_popen.call_args_list[0][0][0][:1])
        self.assertCallArgs([self.make], self.mock_popen.call_args_list[1][0][0][:1])

    def test_install_fails(self):
        self.mock_popen.return_value.returncode = 1
        self.mock_pgconfig.side_effect = fake_pg_config(
            libdir=os.environ['HOME'], bindir='/')

        from pgxnclient.cli import main
        self.assertRaises(PgxnClientException, main, ['install', 'foobar'])

        self.assertEquals(self.mock_popen.call_count, 1)

    def test_install_bad_sha1(self):
        def fakefake(url):
            return fake_get_file(url, urlmap = {
                'http://api.pgxn.org/dist/foobar/0.42.1/META.json':
                'http://api.pgxn.org/dist/foobar/0.42.1/META-badsha1.json'})

        self.mock_get.side_effect = fakefake

        from pgxnclient.cli import main
        from pgxnclient.errors import BadChecksum
        self.assertRaises(BadChecksum,
            main, ['install', '--sudo', '--', 'foobar'])

    def test_install_nosudo(self):
        self.mock_pgconfig.side_effect = fake_pg_config(libdir=os.environ['HOME'])

        from pgxnclient.cli import main
        main(['install', '--nosudo', 'foobar'])

        self.assertEquals(self.mock_popen.call_count, 2)
        self.assertCallArgs([self.make], self.mock_popen.call_args_list[0][0][0][:1])
        self.assertCallArgs([self.make], self.mock_popen.call_args_list[1][0][0][:1])

    def test_install_sudo(self):
        from pgxnclient.cli import main
        main(['install', '--sudo', 'gksudo -d "hello world"', 'foobar'])

        self.assertEquals(self.mock_popen.call_count, 2)
        self.assertCallArgs([self.make],
            self.mock_popen.call_args_list[0][0][0][:1])
        self.assertCallArgs(['gksudo', '-d', 'hello world', self.make],
            self.mock_popen.call_args_list[1][0][0][:4])

    @patch('pgxnclient.tar.TarArchive.unpack')
    def test_install_local_tar(self, mock_unpack):
        fn = get_test_filename('foobar-0.42.1.tar.gz')
        mock_unpack.side_effect = TarArchive(fn).unpack_orig

        from pgxnclient.cli import main
        main(['install', '--sudo', '--', fn])

        self.assertEquals(self.mock_popen.call_count, 2)
        self.assertCallArgs([self.make], self.mock_popen.call_args_list[0][0][0][:1])
        self.assertCallArgs(['sudo', self.make],
            self.mock_popen.call_args_list[1][0][0][:2])
        make_cwd = self.mock_popen.call_args_list[1][1]['cwd']

        self.assertEquals(mock_unpack.call_count, 1)
        tmpdir, = mock_unpack.call_args[0]
        self.assertEqual(make_cwd, os.path.join(tmpdir, 'foobar-0.42.1'))

    @patch('pgxnclient.zip.ZipArchive.unpack')
    def test_install_local_zip(self, mock_unpack):
        fn = get_test_filename('foobar-0.42.1.zip')
        mock_unpack.side_effect = ZipArchive(fn).unpack_orig

        from pgxnclient.cli import main
        main(['install', '--sudo', '--', fn])

        self.assertEquals(self.mock_popen.call_count, 2)
        self.assertCallArgs([self.make], self.mock_popen.call_args_list[0][0][0][:1])
        self.assertCallArgs(['sudo', self.make],
            self.mock_popen.call_args_list[1][0][0][:2])
        make_cwd = self.mock_popen.call_args_list[1][1]['cwd']

        self.assertEquals(mock_unpack.call_count, 1)
        tmpdir, = mock_unpack.call_args[0]
        self.assertEqual(make_cwd, os.path.join(tmpdir, 'foobar-0.42.1'))

    def test_install_url_file(self):
        fn = get_test_filename('foobar-0.42.1.zip')
        url = 'file://' + os.path.abspath(fn).replace("f", '%%%2x' % ord('f'))

        from pgxnclient.cli import main
        main(['install', '--sudo', '--', url])

        self.assertEquals(self.mock_popen.call_count, 2)
        self.assertCallArgs([self.make], self.mock_popen.call_args_list[0][0][0][:1])
        self.assertCallArgs(['sudo', self.make],
            self.mock_popen.call_args_list[1][0][0][:2])

    def test_install_local_dir(self):
        self.mock_get.side_effect = lambda *args: self.fail('network invoked')

        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)

            from pgxnclient.cli import main
            main(['install', '--sudo', '--', dir])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(self.mock_popen.call_count, 2)
        self.assertCallArgs([self.make], self.mock_popen.call_args_list[0][0][0][:1])
        self.assertCallArgs(dir, self.mock_popen.call_args_list[0][1]['cwd'])
        self.assertCallArgs(['sudo', self.make],
            self.mock_popen.call_args_list[1][0][0][:2])
        self.assertEquals(dir, self.mock_popen.call_args_list[1][1]['cwd'])


class CheckTestCase(unittest.TestCase, Assertions):
    def setUp(self):
        self._p1 = patch('pgxnclient.network.get_file')
        self.mock_get = self._p1.start()
        self.mock_get.side_effect = fake_get_file

        self._p2 = patch('pgxnclient.commands.Popen')
        self.mock_popen = self._p2.start()
        self.mock_popen.return_value.returncode = 0

        self._p3 = patch('pgxnclient.commands.WithPgConfig.call_pg_config')
        self.mock_pgconfig = self._p3.start()
        self.mock_pgconfig.side_effect = fake_pg_config(
            libdir='/', bindir='/')

    def tearDown(self):
        self._p1.stop()
        self._p2.stop()
        self._p3.stop()

    def test_check_latest(self):
        from pgxnclient.cli import main
        main(['check', 'foobar'])

        self.assertEquals(self.mock_popen.call_count, 1)
        self.assertCallArgs([self.make], self.mock_popen.call_args_list[0][0][0][:1])

    def test_check_url(self):
        from pgxnclient.cli import main
        main(['check', 'http://api.pgxn.org/dist/foobar/0.42.1/foobar-0.42.1.zip'])

        self.assertEquals(self.mock_popen.call_count, 1)
        self.assertCallArgs([self.make], self.mock_popen.call_args_list[0][0][0][:1])

    def test_check_fails(self):
        self.mock_popen.return_value.returncode = 1

        from pgxnclient.cli import main

        self.assertRaises(PgxnClientException, main, ['check', 'foobar'])

        self.assertEquals(self.mock_popen.call_count, 1)

    def test_check_diff_moved(self):
        def create_regression_files(*args, **kwargs):
            cwd = kwargs['cwd']
            open(os.path.join(cwd, 'regression.out'), 'w').close()
            open(os.path.join(cwd, 'regression.diffs'), 'w').close()
            return Mock()

        self.mock_popen.side_effect = create_regression_files
        self.mock_popen.return_value.returncode = 1

        self.assert_(not os.path.exists('regression.out'),
            "Please remove temp file 'regression.out' from current dir")
        self.assert_(not os.path.exists('regression.diffs'),
            "Please remove temp file 'regression.diffs' from current dir")

        from pgxnclient.cli import main

        try:
            self.assertRaises(PgxnClientException, main, ['check', 'foobar'])
            self.assertEquals(self.mock_popen.call_count, 1)
            self.assert_(os.path.exists('regression.out'))
            self.assert_(os.path.exists('regression.diffs'))
        finally:
            ifunlink('regression.out')
            ifunlink('regression.diffs')

    def test_check_bad_sha1(self):
        def fakefake(url):
            return fake_get_file(url, urlmap = {
                'http://api.pgxn.org/dist/foobar/0.42.1/META.json':
                'http://api.pgxn.org/dist/foobar/0.42.1/META-badsha1.json'})

        self.mock_get.side_effect = fakefake
        self.mock_popen.return_value.returncode = 1

        from pgxnclient.cli import main
        from pgxnclient.errors import BadChecksum
        self.assertRaises(BadChecksum, main, ['check', 'foobar'])

        self.assertEquals(self.mock_popen.call_count, 0)


class LoadTestCase(unittest.TestCase):
    def setUp(self):
        self._p1 = patch('pgxnclient.commands.Popen')
        self.mock_popen = self._p1.start()
        self.mock_popen.return_value.returncode = 0
        self.mock_popen.return_value.communicate.return_value = (b(''), b(''))

        self._p2 = patch('pgxnclient.commands.install.LoadUnload.is_extension')
        self.mock_isext = self._p2.start()
        self.mock_isext.return_value = True

        self._p3 = patch('pgxnclient.commands.install.LoadUnload.get_pg_version')
        self.mock_pgver = self._p3.start()
        self.mock_pgver.return_value = (9,1,0)

    def tearDown(self):
        self._p1.stop()
        self._p2.stop()
        self._p3.stop()

    def test_parse_version(self):
        from pgxnclient.commands.install import Load
        cmd = Load(None)
        self.assertEquals((9,0,3), cmd.parse_pg_version(
            'PostgreSQL 9.0.3 on i686-pc-linux-gnu, compiled by GCC'
            ' gcc-4.4.real (Ubuntu/Linaro 4.4.4-14ubuntu5) 4.4.5, 32-bit'))
        self.assertEquals((9,1,0), cmd.parse_pg_version(
            'PostgreSQL 9.1alpha5 on i686-pc-linux-gnu, compiled by GCC gcc'
            ' (Ubuntu/Linaro 4.4.4-14ubuntu5) 4.4.5, 32-bit '))

    @patch('pgxnclient.network.get_file')
    def test_check_psql_options(self, mock_get):
        mock_get.side_effect = fake_get_file

        from pgxnclient.cli import main

        main(['load', '--yes', '--dbname', 'dbdb', 'foobar'])
        args = self.mock_popen.call_args[0][0]
        self.assertEqual('dbdb', args[args.index('--dbname') + 1])

        main(['load', '--yes', '-U', 'meme', 'foobar'])
        args = self.mock_popen.call_args[0][0]
        self.assertEqual('meme', args[args.index('--username') + 1])

        main(['load', '--yes', '--port', '666', 'foobar'])
        args = self.mock_popen.call_args[0][0]
        self.assertEqual('666', args[args.index('--port') + 1])

        main(['load', '--yes', '-h', 'somewhere', 'foobar'])
        args = self.mock_popen.call_args[0][0]
        self.assertEqual('somewhere', args[args.index('--host') + 1])

    @patch('pgxnclient.zip.ZipArchive.unpack')
    @patch('pgxnclient.network.get_file')
    def test_load_local_zip(self, mock_get, mock_unpack):
        mock_get.side_effect = lambda *args: self.fail('network invoked')
        mock_unpack.side_effect = ZipArchive.unpack_orig

        from pgxnclient.cli import main
        main(['load', '--yes', get_test_filename('foobar-0.42.1.zip')])

        self.assertEquals(mock_unpack.call_count, 0)
        self.assertEquals(self.mock_popen.call_count, 1)
        self.assert_('psql' in self.mock_popen.call_args[0][0][0])
        communicate = self.mock_popen.return_value.communicate
        self.assertEquals(communicate.call_args[0][0],
            b('CREATE EXTENSION foobar;'))

    @patch('pgxnclient.tar.TarArchive.unpack')
    @patch('pgxnclient.network.get_file')
    def test_load_local_tar(self, mock_get, mock_unpack):
        mock_get.side_effect = lambda *args: self.fail('network invoked')
        mock_unpack.side_effect = TarArchive.unpack_orig

        from pgxnclient.cli import main
        main(['load', '--yes', get_test_filename('foobar-0.42.1.tar.gz')])

        self.assertEquals(mock_unpack.call_count, 0)
        self.assertEquals(self.mock_popen.call_count, 1)
        self.assert_('psql' in self.mock_popen.call_args[0][0][0])
        communicate = self.mock_popen.return_value.communicate
        self.assertEquals(communicate.call_args[0][0],
            b('CREATE EXTENSION foobar;'))

    @patch('pgxnclient.network.get_file')
    def test_load_local_dir(self, mock_get):
        mock_get.side_effect = lambda *args: self.fail('network invoked')

        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)

            from pgxnclient.cli import main
            main(['load', '--yes', dir])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(self.mock_popen.call_count, 1)
        self.assert_('psql' in self.mock_popen.call_args[0][0][0])
        communicate = self.mock_popen.return_value.communicate
        self.assertEquals(communicate.call_args[0][0],
            b('CREATE EXTENSION foobar;'))

    @patch('pgxnclient.zip.ZipArchive.unpack')
    @patch('pgxnclient.network.get_file')
    def test_load_zip_url(self, mock_get, mock_unpack):
        mock_get.side_effect = fake_get_file
        mock_unpack.side_effect = ZipArchive.unpack_orig

        from pgxnclient.cli import main
        main(['load', '--yes',
            'http://api.pgxn.org/dist/foobar/0.42.1/foobar-0.42.1.zip'])

        self.assertEquals(mock_unpack.call_count, 0)
        self.assertEquals(self.mock_popen.call_count, 1)
        self.assert_('psql' in self.mock_popen.call_args[0][0][0])
        communicate = self.mock_popen.return_value.communicate
        self.assertEquals(communicate.call_args[0][0],
            b('CREATE EXTENSION foobar;'))

    @patch('pgxnclient.tar.TarArchive.unpack')
    @patch('pgxnclient.network.get_file')
    def test_load_tar_url(self, mock_get, mock_unpack):
        mock_get.side_effect = fake_get_file
        mock_unpack.side_effect = TarArchive.unpack_orig

        from pgxnclient.cli import main
        main(['load', '--yes',
            'http://example.org/foobar-0.42.1.tar.gz'])

        self.assertEquals(mock_unpack.call_count, 0)
        self.assertEquals(self.mock_popen.call_count, 1)
        self.assert_('psql' in self.mock_popen.call_args[0][0][0])
        communicate = self.mock_popen.return_value.communicate
        self.assertEquals(communicate.call_args[0][0],
            b('CREATE EXTENSION foobar;'))

    def test_load_extensions_order(self):
        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)
            shutil.copyfile(
                get_test_filename('META-manyext.json'),
                os.path.join(dir, 'META.json'))

            from pgxnclient.cli import main
            main(['load', '--yes', dir])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(self.mock_popen.call_count, 4)
        self.assert_('psql' in self.mock_popen.call_args[0][0][0])
        communicate = self.mock_popen.return_value.communicate
        self.assertEquals(communicate.call_args_list[0][0][0],
            b('CREATE EXTENSION foo;'))
        self.assertEquals(communicate.call_args_list[1][0][0],
            b('CREATE EXTENSION bar;'))
        self.assertEquals(communicate.call_args_list[2][0][0],
            b('CREATE EXTENSION baz;'))
        self.assertEquals(communicate.call_args_list[3][0][0],
            b('CREATE EXTENSION qux;'))

    def test_unload_extensions_order(self):
        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)
            shutil.copyfile(
                get_test_filename('META-manyext.json'),
                os.path.join(dir, 'META.json'))

            from pgxnclient.cli import main
            main(['unload', '--yes', dir])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(self.mock_popen.call_count, 4)
        self.assert_('psql' in self.mock_popen.call_args[0][0][0])
        communicate = self.mock_popen.return_value.communicate
        self.assertEquals(communicate.call_args_list[0][0][0],
            b('DROP EXTENSION qux;'))
        self.assertEquals(communicate.call_args_list[1][0][0],
            b('DROP EXTENSION baz;'))
        self.assertEquals(communicate.call_args_list[2][0][0],
            b('DROP EXTENSION bar;'))
        self.assertEquals(communicate.call_args_list[3][0][0],
            b('DROP EXTENSION foo;'))

    def test_load_list(self):
        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)
            shutil.copyfile(
                get_test_filename('META-manyext.json'),
                os.path.join(dir, 'META.json'))

            from pgxnclient.cli import main
            main(['load', '--yes', dir, 'baz', 'foo'])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(self.mock_popen.call_count, 2)
        self.assert_('psql' in self.mock_popen.call_args[0][0][0])
        communicate = self.mock_popen.return_value.communicate
        self.assertEquals(communicate.call_args_list[0][0][0],
            b('CREATE EXTENSION baz;'))
        self.assertEquals(communicate.call_args_list[1][0][0],
            b('CREATE EXTENSION foo;'))

    def test_unload_list(self):
        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)
            shutil.copyfile(
                get_test_filename('META-manyext.json'),
                os.path.join(dir, 'META.json'))

            from pgxnclient.cli import main
            main(['unload', '--yes', dir, 'baz', 'foo'])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(self.mock_popen.call_count, 2)
        self.assert_('psql' in self.mock_popen.call_args[0][0][0])
        communicate = self.mock_popen.return_value.communicate
        self.assertEquals(communicate.call_args_list[0][0][0],
            b('DROP EXTENSION baz;'))
        self.assertEquals(communicate.call_args_list[1][0][0],
            b('DROP EXTENSION foo;'))

    def test_load_missing(self):
        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)
            shutil.copyfile(
                get_test_filename('META-manyext.json'),
                os.path.join(dir, 'META.json'))

            from pgxnclient.cli import main
            self.assertRaises(PgxnClientException, main,
                ['load', '--yes', dir, 'foo', 'ach'])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(self.mock_popen.call_count, 0)

    def test_unload_missing(self):
        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)
            shutil.copyfile(
                get_test_filename('META-manyext.json'),
                os.path.join(dir, 'META.json'))

            from pgxnclient.cli import main
            self.assertRaises(PgxnClientException, main,
                ['unload', '--yes', dir, 'foo', 'ach'])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(self.mock_popen.call_count, 0)


class SearchTestCase(unittest.TestCase):
    @patch('sys.stdout')
    @patch('pgxnclient.network.get_file')
    def test_search_quoting(self, mock_get, stdout):
        mock_get.side_effect = fake_get_file
        from pgxnclient.cli import main
        main(['search', '--docs', 'foo bar', 'baz'])


if __name__ == '__main__':
    unittest.main()
