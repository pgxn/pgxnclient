from mock import patch
from unittest2 import TestCase

import os
from urllib import quote

class FakeFile(file):
    url = None
    pass

def fake_get_file(url):
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
        main(['download', 'foobar'])
        self.assert_(os.path.exists(fn))
        os.unlink(fn)

    @patch('pgxn.client.api.get_file')
    def test_download_testing(self, mock):
        mock.side_effect = fake_get_file

        fn = 'foobar-0.43.2b1.pgz'
        self.assert_(not os.path.exists(fn))

        from pgxn.client.cli import main
        main(['download', '--testing', 'foobar'])
        self.assert_(os.path.exists(fn))
        os.unlink(fn)


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


