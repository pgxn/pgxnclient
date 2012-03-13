from pgxnclient.tests import unittest

from pgxnclient import Label, Term, Identifier

class LabelTestCase(unittest.TestCase):
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
            'a_b',
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


class TermTestCase(unittest.TestCase):
    def test_ok(self):
        for s in [
            'aa'
            'adfkjh"()', ]:
            self.assertEqual(Term(s), s)
            self.assertEqual(Term(s), Term(s))
            self.assert_(Term(s) <= Term(s))
            self.assert_(Term(s) >= Term(s))

    def test_bad(self):
        def ar(s):
            try: Term(s)
            except ValueError: pass
            else: self.fail("ValueError not raised: '%s'" % s)

        for s in [
            'a',
            'aa ',
            'a/a',
            'a\\a',
            'a\ta',
            'aa\x01' ]:
            ar(s)


class TestIdentifier(unittest.TestCase):
    def test_nonblank(self):
        self.assertRaises(ValueError, Identifier, "")

    def test_unquoted(self):
        for s in [
            'x',
            'xxxxx',
            'abcxyz_0189',
            'ABCXYZ_0189', ]:
            self.assertEqual(Identifier(s), s)

    def test_quoted(self):
        for s, q in [
            ('x-y', '"x-y"'),
            (' ', '" "'),
            ('x"y', '"x""y"')]:
            self.assertEqual(Identifier(s), q)


if __name__ == '__main__':
    unittest.main()
