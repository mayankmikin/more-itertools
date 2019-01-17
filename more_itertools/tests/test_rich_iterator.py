import itertools as it
import operator
import unittest

from six.moves import range

import more_itertools as mi


class RichIteratorTests(unittest.TestCase):
    """Tests for ``RichIterator()``"""

    def setUp(self):
        rng = range(1, 6)
        self.rich_iters = list(map(mi.RichIterator, [
            rng,
            list(rng),
            iter(rng),
            iter(list(rng)),
        ]))

    def test_iteration(self):
        """Test basic iteration"""
        for ri in self.rich_iters:
            self.assertEqual(next(ri), 1)
            self.assertEqual(next(ri), 2)
            self.assertEqual(list(ri), [3, 4, 5])
            self.assertRaises(StopIteration, next, ri)
            self.assertEqual(list(ri), [])

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
        for ri in self.rich_iters:
            self.assertEqual(list(it.islice(ri.cycle(), 12)),
                             [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2])

    def test_accumulate(self):
        for ri in self.rich_iters:
            self.assertEqual(list(ri.accumulate()), [1, 3, 6, 10, 15])

    def test_accumulate_op(self):
        for ri in self.rich_iters:
            self.assertEqual(list(ri.accumulate(operator.mul)),
                             [1, 2, 6, 24, 120])

    def test_chain(self):
        for ri in self.rich_iters:
            self.assertEqual(list(ri.chain('DEF')),
                             [1, 2, 3, 4, 5, 'D', 'E', 'F'])
