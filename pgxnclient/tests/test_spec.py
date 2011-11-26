from pgxnclient.tests import unittest

from pgxnclient import Spec

class SpecTestCase(unittest.TestCase):
    def test_str(self):
        self.assertEqual(
            str(Spec('foo')), 'foo')
        self.assertEqual(
            str(Spec('foo>2.0')), 'foo>2.0')
        self.assertEqual(
            str(Spec('foo>2.0')), 'foo>2.0')
        self.assertEqual(
            str(Spec(dirname='/foo')), '/foo')
        self.assertEqual(
            str(Spec(dirname='/foo/foo.zip')), '/foo/foo.zip')


if __name__ == '__main__':
    unittest.main()

