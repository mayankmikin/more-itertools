from unittest import TestCase

from six.moves import range

import more_itertools as mi


class RichIteratorTests(TestCase):
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
