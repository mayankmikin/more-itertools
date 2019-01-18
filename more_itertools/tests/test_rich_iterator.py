import itertools as it
import operator
import unittest

from six.moves import range

import more_itertools as mi


class RichIteratorTests(unittest.TestCase):
    """Tests for ``RichIterator()``"""

    @staticmethod
    def rich_iters(iterable=range(1, 6)):
        return list(map(mi.RichIterator, [
            iterable,
            list(iterable),
            iter(iterable),
            iter(list(iterable)),
        ]))

    def test_iteration(self):
        """Test basic iteration"""
        for ri in self.rich_iters():
            self.assertEqual(next(ri), 1)
            self.assertEqual(next(ri), 2)
            self.assertEqual(list(ri), [3, 4, 5])
            self.assertRaises(StopIteration, next, ri)
            self.assertEqual(list(ri), [])

    def test_slicing(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri[:]), [1, 2, 3, 4, 5])
        for ri in self.rich_iters():
            self.assertEqual(list(ri[:2]), [1, 2])
        for ri in self.rich_iters():
            self.assertEqual(list(ri[2:]), [3, 4, 5])
        for ri in self.rich_iters():
            self.assertEqual(list(ri[2:4]), [3, 4])
        for ri in self.rich_iters():
            self.assertEqual(list(ri[::2]), [1, 3, 5])
        for ri in self.rich_iters():
            self.assertEqual(list(ri[1::2]), [2, 4])

    def test_count(self):
        ri = mi.RichIterator.count()
        self.assertEqual(list(it.islice(ri, 5)), [0, 1, 2, 3, 4])

        ri = mi.RichIterator.count(10)
        self.assertEqual(list(it.islice(ri, 5)), [10, 11, 12, 13, 14])

        ri = mi.RichIterator.count(step=2)
        self.assertEqual(list(it.islice(ri, 5)), [0, 2, 4, 6, 8])

        ri = mi.RichIterator.count(10, 2)
        self.assertEqual(list(it.islice(ri, 5)), [10, 12, 14, 16, 18])

    def test_repeat(self):
        ri = mi.RichIterator.repeat(10, 3)
        self.assertEqual(list(ri), [10, 10, 10])

        ri = mi.RichIterator.repeat(10)
        self.assertEqual(list(it.islice(ri, 5)), [10, 10, 10, 10, 10])

    def test_cycle(self):
        for ri in self.rich_iters():
            self.assertEqual(list(it.islice(ri.cycle(), 12)),
                             [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2])

    def test_accumulate(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.accumulate()), [1, 3, 6, 10, 15])
        for ri in self.rich_iters():
            self.assertEqual(list(ri.accumulate(operator.mul)),
                             [1, 2, 6, 24, 120])

    def test_chain(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.chain('DEF')),
                             [1, 2, 3, 4, 5, 'D', 'E', 'F'])

    def test_compress(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.compress([1, 0, 1, 1, 0])), [1, 3, 4])

    def test_dropwhile(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.dropwhile(lambda x: x < 3)), [3, 4, 5])

    def test_filter(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.filter(lambda x: x % 2)), [1, 3, 5])

    def test_filterfalse(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.filterfalse(lambda x: x % 2)), [2, 4])

    def test_groupby(self):
        for ri in self.rich_iters('AAAABBBCCDAABBBB'):
            self.assertEqual([(k, ''.join(g)) for k, g in ri.groupby()],
                             [('A', 'AAAA'), ('B', 'BBB'), ('C', 'CC'),
                              ('D', 'D'), ('A', 'AA'), ('B', 'BBBB')])

        for ri in self.rich_iters('AAAABBBCCDAABBBB'):
            self.assertEqual(
                [(k, ''.join(g)) for k, g in ri.groupby(lambda x: x > 'B')],
                [(False, 'AAAABBB'), (True, 'CCD'), (False, 'AABBBB')])

    def test_map(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.map(operator.neg)), [-1, -2, -3, -4, -5])
        for ri in self.rich_iters():
            self.assertEqual(list(ri.map(pow, reversed(range(1, 6)))),
                             [1, 16, 27, 16, 5])

    def test_stapmap(self):
        iterable = list(zip(range(1, 6), reversed(range(1, 6))))
        for ri in self.rich_iters(iterable):
            self.assertEqual(list(ri.starmap(pow)), [1, 16, 27, 16, 5])

    def test_takewhile(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.takewhile(lambda x: x < 3)), [1, 2])

    def test_tee(self):
        for ri in self.rich_iters():
            it1, it2 = ri.tee()
            self.assertEqual(list(it1), [1, 2, 3, 4, 5])
            self.assertEqual(list(it2), [1, 2, 3, 4, 5])
        for ri in self.rich_iters():
            it1, it2, it3 = ri.tee(3)
            self.assertEqual(list(it1), [1, 2, 3, 4, 5])
            self.assertEqual(list(it2), [1, 2, 3, 4, 5])
            self.assertEqual(list(it3), [1, 2, 3, 4, 5])

    def test_zip(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.zip('xy')), [(1, 'x'), (2, 'y')])
        for ri in self.rich_iters():
            self.assertEqual(list(ri.zip('xyz', [True, False])),
                             [(1, 'x', True), (2, 'y', False)])

    def test_zip_longest(self):
        for ri in self.rich_iters():
            self.assertEqual(list(ri.zip_longest('xy', fillvalue='')),
                             [(1, 'x'), (2, 'y'), (3, ''), (4, ''), (5, '')])
        for ri in self.rich_iters():
            self.assertEqual(list(ri.zip_longest('xyz', [True, False])),
                             [(1, 'x', True), (2, 'y', False), (3, 'z', None),
                              (4, None, None), (5, None, None)])

    def test_permutations(self):
        for ri in self.rich_iters('ABCD'):
            self.assertEqual(list(ri.permutations(2)),
                             list(map(tuple, 'AB AC AD BA BC BD '
                                             'CA CB CD DA DB DC'.split())))
        for ri in self.rich_iters(range(3)):
            self.assertEqual(list(ri.permutations()),
                             [(0, 1, 2), (0, 2, 1), (1, 0, 2),
                              (1, 2, 0), (2, 0, 1), (2, 1, 0)])

    def test_product(self):
        for ri in self.rich_iters('ABCD'):
            self.assertEqual(list(ri.product('xy')),
                             list(map(tuple, 'Ax Ay Bx By '
                                             'Cx Cy Dx Dy'.split())))
        for ri in self.rich_iters(range(2)):
            self.assertEqual(list(ri.product(repeat=3)),
                             [(0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1),
                              (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1)])

    def test_combinations(self):
        for ri in self.rich_iters('ABCD'):
            self.assertEqual(list(ri.combinations(2)),
                             [('A', 'B'), ('A', 'C'), ('A', 'D'),
                              ('B', 'C'), ('B', 'D'), ('C', 'D')])
        for ri in self.rich_iters(range(4)):
            self.assertEqual(list(ri.combinations(3)),
                             [(0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3)])

    def test_combinations_with_replacement(self):
        for ri in self.rich_iters('ABC'):
            self.assertEqual(list(ri.combinations_with_replacement(2)),
                             [('A', 'A'), ('A', 'B'), ('A', 'C'),
                              ('B', 'B'), ('B', 'C'), ('C', 'C')])
