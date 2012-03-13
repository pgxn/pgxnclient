from mock import patch, Mock

import os
import tempfile
import shutil
from urllib import quote

from pgxnclient.utils import b
from pgxnclient.errors import PgxnClientException, ResourceNotFound
from pgxnclient.tests import unittest
from pgxnclient.tests.testutils import ifunlink, get_test_filename

class FakeFile(object):
    def __init__(self, *args):
        self._f = open(*args)
        self.url = None

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


class InfoTestCase(unittest.TestCase):
    def _get_output(self, cmdline):
        @patch('sys.stdout')
        @patch('pgxnclient.api.get_file')
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


class CommandTestCase(unittest.TestCase):
    def test_popen_raises(self):
        from pgxnclient.commands import Command
        c = Command([])
        self.assertRaises(PgxnClientException,
            c.popen, "this-script-doesnt-exist")


class DownloadTestCase(unittest.TestCase):
    @patch('pgxnclient.api.get_file')
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

    @patch('pgxnclient.api.get_file')
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

    @patch('pgxnclient.api.get_file')
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

    @patch('pgxnclient.api.get_file')
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

    @patch('pgxnclient.api.get_file')
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

    @patch('pgxnclient.api.get_file')
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


class InstallTestCase(unittest.TestCase):
    @patch('pgxnclient.commands.Popen')
    @patch('pgxnclient.api.get_file')
    def test_install_latest(self, mock_get, mock_popen):
        mock_get.side_effect = fake_get_file
        pop = mock_popen.return_value
        pop.returncode = 0

        from pgxnclient.cli import main
        main(['install', 'foobar'])

        self.assertEquals(mock_popen.call_count, 2)
        self.assertEquals(['make'], mock_popen.call_args_list[0][0][0][:1])
        self.assertEquals(['sudo', 'make'], mock_popen.call_args_list[1][0][0][:2])

    @patch('pgxnclient.commands.Popen')
    @patch('pgxnclient.api.get_file')
    def test_install_fails(self, mock_get, mock_popen):
        mock_get.side_effect = fake_get_file
        pop = mock_popen.return_value
        pop.returncode = 1

        from pgxnclient.cli import main
        self.assertRaises(PgxnClientException, main, ['install', 'foobar'])

        self.assertEquals(mock_popen.call_count, 1)

    @patch('pgxnclient.commands.Popen')
    @patch('pgxnclient.api.get_file')
    def test_install_bad_sha1(self, mock_get, mock_popen):
        def fakefake(url):
            return fake_get_file(url, urlmap = {
                'http://api.pgxn.org/dist/foobar/0.42.1/META.json':
                'http://api.pgxn.org/dist/foobar/0.42.1/META-badsha1.json'})

        mock_get.side_effect = fakefake
        pop = mock_popen.return_value
        pop.returncode = 0

        from pgxnclient.cli import main
        from pgxnclient.errors import BadChecksum
        self.assertRaises(BadChecksum,
            main, ['install', 'foobar'])

    @patch('pgxnclient.commands.Popen')
    @patch('pgxnclient.api.get_file')
    def test_install_nosudo(self, mock_get, mock_popen):
        mock_get.side_effect = fake_get_file
        pop = mock_popen.return_value
        pop.returncode = 0

        from pgxnclient.cli import main
        main(['install', '--nosudo', 'foobar'])

        self.assertEquals(mock_popen.call_count, 2)
        self.assertEquals(['make'], mock_popen.call_args_list[0][0][0][:1])
        self.assertEquals(['make'], mock_popen.call_args_list[1][0][0][:1])

    @patch('pgxnclient.commands.Popen')
    @patch('pgxnclient.api.get_file')
    def test_install_sudo(self, mock_get, mock_popen):
        mock_get.side_effect = fake_get_file
        pop = mock_popen.return_value
        pop.returncode = 0

        from pgxnclient.cli import main
        main(['install', '--sudo', 'gksudo -d "hello world"', 'foobar'])

        self.assertEquals(mock_popen.call_count, 2)
        self.assertEquals(['make'], mock_popen.call_args_list[0][0][0][:1])
        self.assertEquals(['gksudo', '-d', 'hello world', 'make'],
            mock_popen.call_args_list[1][0][0][:4])

    @patch('pgxnclient.commands.unpack')
    @patch('pgxnclient.commands.Popen')
    @patch('pgxnclient.api.get_file')
    def test_install_local_zip(self, mock_get, mock_popen, mock_unpack):
        mock_get.side_effect = lambda *args: self.fail('network invoked')
        pop = mock_popen.return_value
        pop.returncode = 0
        from pgxnclient.utils.zip import unpack
        mock_unpack.side_effect = unpack

        from pgxnclient.cli import main
        main(['install', get_test_filename('foobar-0.42.1.zip')])

        self.assertEquals(mock_popen.call_count, 2)
        self.assertEquals(['make'], mock_popen.call_args_list[0][0][0][:1])
        self.assertEquals(['sudo', 'make'],
            mock_popen.call_args_list[1][0][0][:2])
        make_cwd = mock_popen.call_args_list[1][1]['cwd']

        self.assertEquals(mock_unpack.call_count, 1)
        zipname, tmpdir = mock_unpack.call_args[0]
        self.assertEqual(zipname, get_test_filename('foobar-0.42.1.zip'))
        self.assertEqual(make_cwd, os.path.join(tmpdir, 'foobar-0.42.1'))

    @patch('pgxnclient.commands.Popen')
    @patch('pgxnclient.api.get_file')
    def test_install_local_dir(self, mock_get, mock_popen):
        mock_get.side_effect = lambda *args: self.fail('network invoked')
        pop = mock_popen.return_value
        pop.returncode = 0

        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.utils.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)

            from pgxnclient.cli import main
            main(['install', dir])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(mock_popen.call_count, 2)
        self.assertEquals(['make'], mock_popen.call_args_list[0][0][0][:1])
        self.assertEquals(dir, mock_popen.call_args_list[0][1]['cwd'])
        self.assertEquals(['sudo', 'make'],
            mock_popen.call_args_list[1][0][0][:2])
        self.assertEquals(dir, mock_popen.call_args_list[1][1]['cwd'])


class CheckTestCase(unittest.TestCase):
    @patch('pgxnclient.commands.Popen')
    @patch('pgxnclient.api.get_file')
    def test_check_latest(self, mock_get, mock_popen):
        mock_get.side_effect = fake_get_file
        pop = mock_popen.return_value
        pop.returncode = 0

        from pgxnclient.cli import main
        main(['check', 'foobar'])

        self.assertEquals(mock_popen.call_count, 1)
        self.assertEquals(['make'], mock_popen.call_args_list[0][0][0][:1])

    @patch('pgxnclient.commands.Popen')
    @patch('pgxnclient.api.get_file')
    def test_check_fails(self, mock_get, mock_popen):
        mock_get.side_effect = fake_get_file
        pop = mock_popen.return_value
        pop.returncode = 1

        from pgxnclient.cli import main

        self.assertRaises(PgxnClientException, main, ['check', 'foobar'])

        self.assertEquals(mock_popen.call_count, 1)

    @patch('pgxnclient.commands.Popen')
    @patch('pgxnclient.api.get_file')
    def test_check_diff_moved(self, mock_get, mock_popen):
        mock_get.side_effect = fake_get_file

        def create_regression_files(*args, **kwargs):
            cwd = kwargs['cwd']
            open(os.path.join(cwd, 'regression.out'), 'w').close()
            open(os.path.join(cwd, 'regression.diffs'), 'w').close()
            return Mock()

        mock_popen.side_effect = create_regression_files
        pop = mock_popen.return_value
        pop.returncode = 1

        self.assert_(not os.path.exists('regression.out'),
            "Please remove temp file 'regression.out' from current dir")
        self.assert_(not os.path.exists('regression.diffs'),
            "Please remove temp file 'regression.diffs' from current dir")

        from pgxnclient.cli import main

        try:
            self.assertRaises(PgxnClientException, main, ['check', 'foobar'])
            self.assertEquals(mock_popen.call_count, 1)
            self.assert_(os.path.exists('regression.out'))
            self.assert_(os.path.exists('regression.diffs'))
        finally:
            ifunlink('regression.out')
            ifunlink('regression.diffs')

    @patch('pgxnclient.commands.Popen')
    @patch('pgxnclient.api.get_file')
    def test_check_bad_sha1(self, mock_get, mock_popen):
        def fakefake(url):
            return fake_get_file(url, urlmap = {
                'http://api.pgxn.org/dist/foobar/0.42.1/META.json':
                'http://api.pgxn.org/dist/foobar/0.42.1/META-badsha1.json'})

        mock_get.side_effect = fakefake
        pop = mock_popen.return_value
        pop.returncode = 1

        from pgxnclient.cli import main
        from pgxnclient.errors import BadChecksum
        self.assertRaises(BadChecksum, main, ['check', 'foobar'])

        self.assertEquals(mock_popen.call_count, 0)


class LoadTestCase(unittest.TestCase):
    def test_parse_version(self):
        from pgxnclient.commands.install import Load
        cmd = Load(None)
        self.assertEquals((9,0,3), cmd.parse_pg_version(
            'PostgreSQL 9.0.3 on i686-pc-linux-gnu, compiled by GCC'
            ' gcc-4.4.real (Ubuntu/Linaro 4.4.4-14ubuntu5) 4.4.5, 32-bit'))
        self.assertEquals((9,1,0), cmd.parse_pg_version(
            'PostgreSQL 9.1alpha5 on i686-pc-linux-gnu, compiled by GCC gcc'
            ' (Ubuntu/Linaro 4.4.4-14ubuntu5) 4.4.5, 32-bit '))

    @patch('pgxnclient.commands.install.Load.is_extension')
    @patch('pgxnclient.commands.install.Load.get_pg_version')
    @patch('pgxnclient.commands.Popen')
    @patch('pgxnclient.api.get_file')
    def test_check_psql_options(self,
            mock_get, mock_popen, mock_pgver, mock_isext):
        mock_get.side_effect = fake_get_file
        pop = mock_popen.return_value
        pop.returncode = 0
        pop.communicate.return_value = (b(''), b(''))
        mock_pgver.return_value = (9,1,0)
        mock_isext.return_value = True

        from pgxnclient.cli import main

        main(['load', '--yes', '--dbname', 'dbdb', 'foobar'])
        args = mock_popen.call_args[0][0]
        self.assertEqual('dbdb', args[args.index('--dbname') + 1])

        main(['load', '--yes', '-U', 'meme', 'foobar'])
        args = mock_popen.call_args[0][0]
        self.assertEqual('meme', args[args.index('--username') + 1])

        main(['load', '--yes', '--port', '666', 'foobar'])
        args = mock_popen.call_args[0][0]
        self.assertEqual('666', args[args.index('--port') + 1])

        main(['load', '--yes', '-h', 'somewhere', 'foobar'])
        args = mock_popen.call_args[0][0]
        self.assertEqual('somewhere', args[args.index('--host') + 1])

    @patch('pgxnclient.commands.install.Load.is_extension')
    @patch('pgxnclient.commands.install.Load.get_pg_version')
    @patch('pgxnclient.commands.unpack')
    @patch('pgxnclient.commands.Popen')
    @patch('pgxnclient.api.get_file')
    def test_load_local_zip(self, mock_get, mock_popen, mock_unpack,
            mock_pgver, mock_isext):
        mock_get.side_effect = lambda *args: self.fail('network invoked')
        pop = mock_popen.return_value
        pop.returncode = 0
        from pgxnclient.utils.zip import unpack
        mock_unpack.side_effect = unpack
        mock_pgver.return_value = (9,1,0)
        mock_isext.return_value = True

        from pgxnclient.cli import main
        main(['load', '--yes', get_test_filename('foobar-0.42.1.zip')])

        self.assertEquals(mock_unpack.call_count, 0)
        self.assertEquals(mock_popen.call_count, 1)
        self.assert_('psql' in mock_popen.call_args[0][0][0])
        self.assertEquals(pop.communicate.call_args[0][0],
            'CREATE EXTENSION foobar;')

    @patch('pgxnclient.commands.install.Load.is_extension')
    @patch('pgxnclient.commands.install.Load.get_pg_version')
    @patch('pgxnclient.commands.Popen')
    @patch('pgxnclient.api.get_file')
    def test_load_local_dir(self, mock_get, mock_popen,
            mock_pgver, mock_isext):
        mock_get.side_effect = lambda *args: self.fail('network invoked')
        pop = mock_popen.return_value
        pop.returncode = 0
        mock_pgver.return_value = (9,1,0)
        mock_isext.return_value = True

        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.utils.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)

            from pgxnclient.cli import main
            main(['load', '--yes', dir])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(mock_popen.call_count, 1)
        self.assert_('psql' in mock_popen.call_args[0][0][0])
        self.assertEquals(pop.communicate.call_args[0][0],
            'CREATE EXTENSION foobar;')

    @patch('pgxnclient.commands.install.Load.is_extension')
    @patch('pgxnclient.commands.install.Load.get_pg_version')
    @patch('pgxnclient.commands.Popen')
    def test_load_extensions_order(self, mock_popen, mock_pgver, mock_isext):
        pop = mock_popen.return_value
        pop.returncode = 0
        mock_pgver.return_value = (9,1,0)
        mock_isext.return_value = True

        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.utils.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)
            shutil.copyfile(
                get_test_filename('META-manyext.json'),
                os.path.join(dir, 'META.json'))

            from pgxnclient.cli import main
            main(['load', '--yes', dir])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(mock_popen.call_count, 4)
        self.assert_('psql' in mock_popen.call_args[0][0][0])
        self.assertEquals(pop.communicate.call_args_list[0][0][0],
            'CREATE EXTENSION foo;')
        self.assertEquals(pop.communicate.call_args_list[1][0][0],
            'CREATE EXTENSION bar;')
        self.assertEquals(pop.communicate.call_args_list[2][0][0],
            'CREATE EXTENSION baz;')
        self.assertEquals(pop.communicate.call_args_list[3][0][0],
            'CREATE EXTENSION qux;')

    @patch('pgxnclient.commands.install.Unload.is_extension')
    @patch('pgxnclient.commands.install.Unload.get_pg_version')
    @patch('pgxnclient.commands.Popen')
    def test_unload_extensions_order(self, mock_popen, mock_pgver, mock_isext):
        pop = mock_popen.return_value
        pop.returncode = 0
        mock_pgver.return_value = (9,1,0)
        mock_isext.return_value = True

        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.utils.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)
            shutil.copyfile(
                get_test_filename('META-manyext.json'),
                os.path.join(dir, 'META.json'))

            from pgxnclient.cli import main
            main(['unload', '--yes', dir])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(mock_popen.call_count, 4)
        self.assert_('psql' in mock_popen.call_args[0][0][0])
        self.assertEquals(pop.communicate.call_args_list[0][0][0],
            'DROP EXTENSION qux;')
        self.assertEquals(pop.communicate.call_args_list[1][0][0],
            'DROP EXTENSION baz;')
        self.assertEquals(pop.communicate.call_args_list[2][0][0],
            'DROP EXTENSION bar;')
        self.assertEquals(pop.communicate.call_args_list[3][0][0],
            'DROP EXTENSION foo;')

    @patch('pgxnclient.commands.install.Load.is_extension')
    @patch('pgxnclient.commands.install.Load.get_pg_version')
    @patch('pgxnclient.commands.Popen')
    def test_load_list(self, mock_popen, mock_pgver, mock_isext):
        pop = mock_popen.return_value
        pop.returncode = 0
        mock_pgver.return_value = (9,1,0)
        mock_isext.return_value = True

        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.utils.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)
            shutil.copyfile(
                get_test_filename('META-manyext.json'),
                os.path.join(dir, 'META.json'))

            from pgxnclient.cli import main
            main(['load', '--yes', dir, 'baz', 'foo'])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(mock_popen.call_count, 2)
        self.assert_('psql' in mock_popen.call_args[0][0][0])
        self.assertEquals(pop.communicate.call_args_list[0][0][0],
            'CREATE EXTENSION baz;')
        self.assertEquals(pop.communicate.call_args_list[1][0][0],
            'CREATE EXTENSION foo;')

    @patch('pgxnclient.commands.install.Unload.is_extension')
    @patch('pgxnclient.commands.install.Unload.get_pg_version')
    @patch('pgxnclient.commands.Popen')
    def test_unload_list(self, mock_popen, mock_pgver, mock_isext):
        pop = mock_popen.return_value
        pop.returncode = 0
        mock_pgver.return_value = (9,1,0)
        mock_isext.return_value = True

        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.utils.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)
            shutil.copyfile(
                get_test_filename('META-manyext.json'),
                os.path.join(dir, 'META.json'))

            from pgxnclient.cli import main
            main(['unload', '--yes', dir, 'baz', 'foo'])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(mock_popen.call_count, 2)
        self.assert_('psql' in mock_popen.call_args[0][0][0])
        self.assertEquals(pop.communicate.call_args_list[0][0][0],
            'DROP EXTENSION baz;')
        self.assertEquals(pop.communicate.call_args_list[1][0][0],
            'DROP EXTENSION foo;')

    @patch('pgxnclient.commands.install.Load.is_extension')
    @patch('pgxnclient.commands.install.Load.get_pg_version')
    @patch('pgxnclient.commands.Popen')
    def test_load_missing(self, mock_popen, mock_pgver, mock_isext):
        pop = mock_popen.return_value
        pop.returncode = 0
        mock_pgver.return_value = (9,1,0)
        mock_isext.return_value = True

        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.utils.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)
            shutil.copyfile(
                get_test_filename('META-manyext.json'),
                os.path.join(dir, 'META.json'))

            from pgxnclient.cli import main
            self.assertRaises(PgxnClientException, main,
                ['load', '--yes', dir, 'foo', 'ach'])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(mock_popen.call_count, 0)

    @patch('pgxnclient.commands.install.Unload.is_extension')
    @patch('pgxnclient.commands.install.Unload.get_pg_version')
    @patch('pgxnclient.commands.Popen')
    def test_unload_missing(self, mock_popen, mock_pgver, mock_isext):
        pop = mock_popen.return_value
        pop.returncode = 0
        mock_pgver.return_value = (9,1,0)
        mock_isext.return_value = True

        tdir = tempfile.mkdtemp()
        try:
            from pgxnclient.utils.zip import unpack
            dir = unpack(get_test_filename('foobar-0.42.1.zip'), tdir)
            shutil.copyfile(
                get_test_filename('META-manyext.json'),
                os.path.join(dir, 'META.json'))

            from pgxnclient.cli import main
            self.assertRaises(PgxnClientException, main,
                ['unload', '--yes', dir, 'foo', 'ach'])

        finally:
            shutil.rmtree(tdir)

        self.assertEquals(mock_popen.call_count, 0)


class SearchTestCase(unittest.TestCase):
    @patch('sys.stdout')
    @patch('pgxnclient.api.get_file')
    def test_search_quoting(self, mock_get, stdout):
        mock_get.side_effect = fake_get_file
        from pgxnclient.cli import main
        main(['search', '--docs', 'foo bar', 'baz'])


if __name__ == '__main__':
    unittest.main()
