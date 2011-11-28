from pgxnclient.tests import unittest

from pgxnclient import SemVer

class SemVerTestCase(unittest.TestCase):
    def test_ok(self):
        for s in [
            '1.2.2',
            '0.2.2',
            '1.2.2',
            '0.0.0',
            '0.1.999',
            '9999.9999999.823823',
            '1.0.0beta1',
            '1.0.0beta2',
            '1.0.0',
            '20110204.0.0', ]:
            self.assertEqual(SemVer(s), s)

    def test_bad(self):
        def ar(s):
            try: SemVer(s)
            except ValueError: pass
            else: self.fail("ValueError not raised: '%s'" % s)

        for s in [
           '1.2',
           '1.2.02',
           '1.2.2-',
           '1.2.3b#5',
           '03.3.3',
           'v1.2.2',
           '1.3b',
           '1.4b.0',
           '1v',
           '1v.2.2v',
           '1.2.4b.5', ]:
            ar(s)

    def test_eq(self):
        for s1, s2 in [
            ('1.2.2',  '1.2.2'),
            ('1.2.23', '1.2.23'),
            ('0.0.0', '0.0.0'),
            ('999.888.7777', '999.888.7777'),
            ('0.1.2beta3', '0.1.2beta3'),
            ('1.0.0rc-1', '1.0.0RC-1'), ]:
            self.assertEqual(SemVer(s1), SemVer(s2))
            self.assertEqual(hash(SemVer(s1)), hash(SemVer(s2)))
            self.assert_(SemVer(s1) <= SemVer(s2),
                "%s <= %s failed" % (s1, s2))
            self.assert_(SemVer(s1) >= SemVer(s2),
                "%s >= %s failed" % (s1, s2))

    def test_ne(self):
        for s1, s2 in [
            ('1.2.2', '1.2.3'),
            ('0.0.1', '1.0.0'),
            ('1.0.1', '1.1.0'),
            ('1.1.1', '1.1.0'),
            ('1.2.3b', '1.2.3'),
            ('1.2.3', '1.2.3b'),
            ('1.2.3a', '1.2.3b'),
            ('1.2.3aaaaaaa1', '1.2.3aaaaaaa2'), ]:
            self.assertNotEqual(SemVer(s1), SemVer(s2))
            self.assertNotEqual(hash(SemVer(s1)), hash(SemVer(s2)))

    def test_dis(self):
        for s1, s2 in [
            ('2.2.2', '1.1.1'),
            ('2.2.2', '2.1.1'),
            ('2.2.2', '2.2.1'),
            ('2.2.2b', '2.2.1'),
            ('2.2.2', '2.2.2b'),
            ('2.2.2c', '2.2.2b'),
            ('2.2.2rc-2', '2.2.2RC-1'),
            ('0.9.10', '0.9.9'), ]:
            self.assert_(SemVer(s1) >= SemVer(s2),
                "%s >= %s failed" % (s1, s2))
            self.assert_(SemVer(s1) > SemVer(s2),
                "%s > %s failed" % (s1, s2))
            self.assert_(SemVer(s2) <= SemVer(s1),
                "%s <= %s failed" % (s2, s1))
            self.assert_(SemVer(s2) < SemVer(s1),
                "%s < %s failed" % (s2, s1))

    def test_clean(self):
        for s1, s2 in [
            ('1.2.2',          '1.2.2'),
            ('01.2.2',         '1.2.2'),
            ('1.02.2',         '1.2.2'),
            ('1.2.02',         '1.2.2'),
            ('1.2.02b',        '1.2.2b'),
            ('1.2.02beta-3  ', '1.2.2beta-3'),
            ('1.02.02rc1',     '1.2.2rc1'),
            ('1.0',            '1.0.0'),
            ('1',              '1.0.0'),
            ('.0.02',          '0.0.2'),
            ('1..02',          '1.0.2'),
            ('1..',            '1.0.0'),
            ('1.1',            '1.1.0'),
            ('1.2.b1',         '1.2.0b1'),
            ('9.0beta4',       '9.0.0beta4'), # PostgreSQL format.
            ('9b',             '9.0.0b'),
            ('rc1',            '0.0.0rc1'),
            ('',               '0.0.0'),
            ('..2',            '0.0.2'),
            ('1.2.3 a',        '1.2.3a'),
            ('..2 b',          '0.0.2b'),
            ('  012.2.2',      '12.2.2'),
            ('20110204',  '20110204.0.0'), ]:
            self.assertEqual(SemVer.clean(s1), SemVer(s2))

    def test_cant_clean(self):
        def ar(s):
            try: SemVer.clean(s)
            except ValueError: pass
            else: self.fail("ValueError not raised: '%s'" % s)

        for s in [
           '1.2.0 beta 4',
           '1.2.2-',
           '1.2.3b#5',
           'v1.2.2',
           '1.4b.0',
           '1v.2.2v',
           '1.2.4b.5',
           '1.2.3.4',
           '1.2.3 4',
           '1.2000000000000000.3.4',]:
            ar(s)


if __name__ == '__main__':
    unittest.main()
