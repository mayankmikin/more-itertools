import itertools as it

import six


class RichIterator(six.Iterator):
    """Wrapper of iterables exposing several convenience methods and operators."""

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
        return cls(it.repeat(object, times))
