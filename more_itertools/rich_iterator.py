import itertools as it
import operator

import six

from . import recipes


class RichIterator(six.Iterator):
    """Iterable wrapper exposing several convenience methods and operators."""

    __slots__ = ('_it',)

    def __init__(self, iterable):
        self._it = iter(iterable)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._it)

    @classmethod
    def count(cls, start=0, step=1):
        return cls(it.count(start, step))

    @classmethod
    def repeat(cls, object, times=None):
        return cls(it.repeat(object, times) if times is not None else
                   it.repeat(object))

    def cycle(self):
        return self._wrap(it.cycle)

    def accumulate(self, func=operator.add):
        return self._wrap(_accumulate, func)

    def chain(self, *iterables):
        return self._wrap(it.chain, *iterables)

    def compress(self, selectors):
        return self._wrap(it.compress, selectors)

    def dropwhile(self, predicate):
        return self._wrap1(it.dropwhile, predicate)

    def filter(self, predicate):
        return self._wrap1(_filter, predicate)

    def filterfalse(self, predicate):
        return self._wrap1(_filterfalse, predicate)

    def groupby(self, key=None):
        return self._wrap(it.groupby, key)

    def map(self, func, *iterables):
        return self._wrap1(_map, func, *iterables)

    def starmap(self, func):
        return self._wrap1(it.starmap, func)

    def takewhile(self, predicate):
        return self._wrap1(it.takewhile, predicate)

    def tee(self, n=2):
        return self._wrap(it.tee, n)

    def zip(self, *iterables):
        return self._wrap(_zip, *iterables)

    def zip_longest(self, *iterables, **kwargs):
        return self._wrap(_zip_longest, *iterables, **kwargs)

    def _wrap(self, func, *args, **kwargs):
        return self.__class__(func(self._it, *args, **kwargs))

    def _wrap1(self, func, *args, **kwargs):
        return self.__class__(func(args[0], self._it, *args[1:], **kwargs))


_accumulate = getattr(it, 'accumulate', recipes.accumulate)
_filter = six.moves.filter
_filterfalse = six.moves.filterfalse
_map = six.moves.map
_zip = six.moves.zip
_zip_longest = six.moves.zip_longest
