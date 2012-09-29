from pgxnclient import tar
from pgxnclient import zip
from pgxnclient import archive

from pgxnclient.tests import unittest
from pgxnclient.errors import PgxnClientException
from pgxnclient.tests.testutils import get_test_filename

class TestArchive(unittest.TestCase):
    def test_from_file_zip(self):
        fn = get_test_filename('foobar-0.42.1.zip')
        a = archive.from_file(fn)
        self.assert_(isinstance(a, zip.ZipArchive))
        self.assertEqual(a.filename, fn)

    def test_from_file_tar(self):
        fn = get_test_filename('foobar-0.42.1.tar.gz')
        a = archive.from_file(fn)
        self.assert_(isinstance(a, tar.TarArchive))
        self.assertEqual(a.filename, fn)

    def test_from_file_unknown(self):
        fn = get_test_filename('META-manyext.json')
        self.assertRaises(PgxnClientException(archive.from_file, fn))


class TestZipArchive(unittest.TestCase):
    def test_can_open(self):
        fn = get_test_filename('foobar-0.42.1.zip')
        a = zip.ZipArchive(fn)
        self.assert_(a.can_open())
        a.open()
        a.close()

    def test_can_open_noext(self):
        fn = get_test_filename('zip.ext')
        a = zip.ZipArchive(fn)
        self.assert_(a.can_open())
        a.open()
        a.close()

    def test_cannot_open(self):
        fn = get_test_filename('foobar-0.42.1.tar.gz')
        a = zip.ZipArchive(fn)
        self.assert_(not a.can_open())


class TestTarArchive(unittest.TestCase):
    def test_can_open(self):
        fn = get_test_filename('foobar-0.42.1.tar.gz')
        a = tar.TarArchive(fn)
        self.assert_(a.can_open())
        a.open()
        a.close()

    def test_can_open_noext(self):
        fn = get_test_filename('tar.ext')
        a = tar.TarArchive(fn)
        self.assert_(a.can_open())
        a.open()
        a.close()

    def test_cannot_open(self):
        fn = get_test_filename('foobar-0.42.1.zip')
        a = tar.TarArchive(fn)
        self.assert_(not a.can_open())

