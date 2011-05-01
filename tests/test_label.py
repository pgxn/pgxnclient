from unittest2 import TestCase

from pgxnclient import Label

class LabelTestCase(TestCase):
    def test_ok(self):
        for s in [
            'd',
            'a1234',
            'abcd1234-5432XYZ',
            'a12345678901234567890123456789012345678901234567890123456789012',]:
            self.assertEqual(Label(s), s)
            self.assertEqual(Label(s), Label(s))
            self.assert_(Label(s) <= Label(s))
            self.assert_(Label(s) >= Label(s))

    def test_bad(self):
        def ar(s):
            try: Label(s)
            except ValueError: pass
            else: self.fail("ValueError not raised: '%s'" % s)

        for s in [
            '',
            ' a',
            'a ',
            '1a',
            '-a',
            'a-',
            'a123456789012345678901234567890123456789012345678901234567890123',]:
            ar(s)

    def test_compare(self):
        self.assertEqual(Label('a'), Label('A'))
        self.assertNotEqual(str(Label('a')), str(Label('A')))   # preserving

    def test_order(self):
        self.assert_(Label('a') < Label('B') < Label('c'))
        self.assert_(Label('A') < Label('b') < Label('C'))
        self.assert_(Label('a') <= Label('B') <= Label('c'))
        self.assert_(Label('A') <= Label('b') <= Label('C'))
        self.assert_(Label('c') > Label('B') > Label('a'))
        self.assert_(Label('C') > Label('b') > Label('A'))
        self.assert_(Label('c') >= Label('B') >= Label('a'))
        self.assert_(Label('C') >= Label('b') >= Label('A'))

