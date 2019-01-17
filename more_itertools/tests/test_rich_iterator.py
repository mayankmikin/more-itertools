import itertools as it
import unittest

from six.moves import range

import more_itertools as mi


class RichIteratorTests(unittest.TestCase):
    """Tests for ``RichIterator()``"""

    def setUp(self):
        rng = range(10)
        self.iterables = [
            rng,
            list(rng),
            iter(rng),
            iter(list(rng)),
        ]

    def test_iteration(self):
        """Test basic iteration"""
        for iterable in self.iterables:
            ri = mi.RichIterator(iterable)
            self.assertEqual(next(ri), 0)
            self.assertEqual(next(ri), 1)
            self.assertEqual(list(ri), list(range(2, 10)))
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
