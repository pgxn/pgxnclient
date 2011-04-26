from mock import patch, Mock
from unittest2 import TestCase

import os
from urllib import quote

from testutils import ifunlink

class FakeFile(file):
    url = None
    pass

def fake_get_file(url, urlmap=None):
    if urlmap: url = urlmap.get(url, url)
    fn = os.path.dirname(__file__) + "/data/" + quote(url, safe="")
    f = FakeFile(fn, 'rb')
    f.url = url
    return f

class DownloadTestCase(TestCase):
    @patch('pgxn.client.api.get_file')
    def test_download_latest(self, mock):
        mock.side_effect = fake_get_file

        fn = 'foobar-0.42.1.pgz'
        self.assert_(not os.path.exists(fn))

        from pgxn.client.cli import main
        try:
            main(['download', 'foobar'])
            self.assert_(os.path.exists(fn))
        finally:
            ifunlink(fn)

    @patch('pgxn.client.api.get_file')
    def test_download_testing(self, mock):
        mock.side_effect = fake_get_file

        fn = 'foobar-0.43.2b1.pgz'
        self.assert_(not os.path.exists(fn))

        from pgxn.client.cli import main
        try:
            main(['download', '--testing', 'foobar'])
            self.assert_(os.path.exists(fn))
        finally:
            ifunlink(fn)

    @patch('pgxn.client.api.get_file')
    def test_download_rename(self, mock):
        mock.side_effect = fake_get_file

        fn = 'foobar-0.42.1.pgz'
        fn1= 'foobar-0.42.1-1.pgz'
        fn2= 'foobar-0.42.1-2.pgz'

        for tmp in (fn, fn1, fn2):
            self.assert_(not os.path.exists(tmp))

        try:
            f = open(fn, "w")
            f.write('test')
            f.close()

            from pgxn.client.cli import main
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

    @patch('pgxn.client.api.get_file')
    def test_download_bad_sha1(self, mock):
        def fakefake(url):
            return fake_get_file(url, urlmap = {
                'http://api.pgxn.org/dist/foobar.json':
                'http://api.pgxn.org/dist/foobar-badsha1.json'})

        mock.side_effect = fakefake

        fn = 'foobar-0.42.1.pgz'
        self.assert_(not os.path.exists(fn))

        try:
            from pgxn.client.cli import main
            from pgxn.client.errors import BadChecksum
            e = self.assertRaises(BadChecksum,
                main, ['download', 'foobar'])

            self.assert_(not os.path.exists(fn))

        finally:
            ifunlink(fn)

class InstallTestCase(TestCase):
    @patch('pgxn.client.commands.Popen')
    @patch('pgxn.client.api.get_file')
    def test_install_latest(self, mock_get, mock_popen):
        mock_get.side_effect = fake_get_file
        pop = mock_popen.return_value
        pop.returncode = 0

        from pgxn.client.cli import main
        main(['install', 'foobar'])

        self.assertEquals(mock_popen.call_count, 2)
        for i, (args, kw) in enumerate(mock_popen.call_args_list):
            self.assertTrue(args[0].startswith('make'))

    @patch('pgxn.client.commands.Popen')
    @patch('pgxn.client.api.get_file')
    def test_install_fails(self, mock_get, mock_popen):
        mock_get.side_effect = fake_get_file
        pop = mock_popen.return_value
        pop.returncode = 1

        from pgxn.client.cli import main
        from pgxn.client.errors import PgxnClientException

        self.assertRaises(PgxnClientException, main, ['install', 'foobar'])

        self.assertEquals(mock_popen.call_count, 1)

    @patch('pgxn.client.commands.Popen')
    @patch('pgxn.client.api.get_file')
    def test_install_bad_sha1(self, mock_get, mock_popen):
        def fakefake(url):
            return fake_get_file(url, urlmap = {
                'http://api.pgxn.org/dist/foobar.json':
                'http://api.pgxn.org/dist/foobar-badsha1.json'})

        mock_get.side_effect = fakefake
        pop = mock_popen.return_value
        pop.returncode = 0

        from pgxn.client.cli import main
        from pgxn.client.errors import BadChecksum
        self.assertRaises(BadChecksum,
            main, ['install', 'foobar'])


class CheckTestCase(TestCase):
    @patch('pgxn.client.commands.Popen')
    @patch('pgxn.client.api.get_file')
    def test_check_latest(self, mock_get, mock_popen):
        mock_get.side_effect = fake_get_file
        pop = mock_popen.return_value
        pop.returncode = 0

        from pgxn.client.cli import main
        main(['check', 'foobar'])

        self.assertEquals(mock_popen.call_count, 1)
        for i, (args, kw) in enumerate(mock_popen.call_args_list):
            self.assertTrue(args[0].startswith('make'))

    @patch('pgxn.client.commands.Popen')
    @patch('pgxn.client.api.get_file')
    def test_check_fails(self, mock_get, mock_popen):
        mock_get.side_effect = fake_get_file
        pop = mock_popen.return_value
        pop.returncode = 1

        from pgxn.client.cli import main
        from pgxn.client.errors import PgxnClientException

        self.assertRaises(PgxnClientException, main, ['check', 'foobar'])

        self.assertEquals(mock_popen.call_count, 1)

    @patch('pgxn.client.commands.Popen')
    @patch('pgxn.client.api.get_file')
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

        from pgxn.client.cli import main
        from pgxn.client.errors import PgxnClientException

        try:
            self.assertRaises(PgxnClientException, main, ['check', 'foobar'])
            self.assertEquals(mock_popen.call_count, 1)
            self.assert_(os.path.exists('regression.out'))
            self.assert_(os.path.exists('regression.diffs'))
        finally:
            ifunlink('regression.out')
            ifunlink('regression.diffs')

    @patch('pgxn.client.commands.Popen')
    @patch('pgxn.client.api.get_file')
    def test_check_bad_sha1(self, mock_get, mock_popen):
        def fakefake(url):
            return fake_get_file(url, urlmap = {
                'http://api.pgxn.org/dist/foobar.json':
                'http://api.pgxn.org/dist/foobar-badsha1.json'})

        mock_get.side_effect = fakefake
        pop = mock_popen.return_value
        pop.returncode = 1

        from pgxn.client.cli import main
        from pgxn.client.errors import BadChecksum
        self.assertRaises(BadChecksum, main, ['check', 'foobar'])

        self.assertEquals(mock_popen.call_count, 0)


class LoadTestCase(TestCase):
    def test_parse_version(self):
        from pgxn.client.commands import Load
        cmd = Load(None)
        self.assertEquals((9,0,3), cmd.parse_pg_version(
            'PostgreSQL 9.0.3 on i686-pc-linux-gnu, compiled by GCC'
            ' gcc-4.4.real (Ubuntu/Linaro 4.4.4-14ubuntu5) 4.4.5, 32-bit'))
        self.assertEquals((9,1,0), cmd.parse_pg_version(
            'PostgreSQL 9.1alpha5 on i686-pc-linux-gnu, compiled by GCC gcc'
            ' (Ubuntu/Linaro 4.4.4-14ubuntu5) 4.4.5, 32-bit '))

