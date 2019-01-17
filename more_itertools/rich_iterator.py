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

    def groupby(self, key=None):
        return self._wrap(it.groupby, key)

    def tee(self, n=2):
        return self._wrap(it.tee, n)

    def _wrap(self, func, *args):
        return self.__class__(func(self._it, *args))


_accumulate = getattr(it, 'accumulate', recipes.accumulate)
