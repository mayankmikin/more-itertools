import itertools as it
import operator

import six
from six.moves import filter, filterfalse, map, zip, zip_longest
try:
    accumulate = it.accumulate
except AttributeError:
    from .recipes import accumulate


__all__ = ['RichIterator']


class RichIterator(six.Iterator):
    """Iterable wrapper exposing several convenience methods and operators."""

    __slots__ = ('_it',)

    def __init__(self, iterable):
        self._it = iter(iterable)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._it)

    def __getitem__(self, index):
        if isinstance(index, int):
            try:
                return next(it.islice(self._it, index, None))
            except StopIteration:
                raise IndexError('index out of range')
        return self._wrap(it.islice, index.start, index.stop, index.step)

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
        return self._wrap(accumulate, func)

    @property
    def chain(self):
        return RichIteratorChain(self)

    def compress(self, selectors):
        return self._wrap(it.compress, selectors)

    def dropwhile(self, predicate):
        return self._wrap1(it.dropwhile, predicate)

    def filter(self, predicate):
        return self._wrap1(filter, predicate)

    def filterfalse(self, predicate):
        return self._wrap1(filterfalse, predicate)

    def groupby(self, key=None):
        return self._wrap(it.groupby, key)

    def map(self, func, *iterables):
        return self._wrap1(map, func, *iterables)

    def starmap(self, func):
        return self._wrap1(it.starmap, func)

    def takewhile(self, predicate):
        return self._wrap1(it.takewhile, predicate)

    def tee(self, n=2):
        return self._wrap(it.tee, n)

    def zip(self, *iterables):
        return self._wrap(zip, *iterables)

    def zip_longest(self, *iterables, **kwargs):
        return self._wrap(zip_longest, *iterables, **kwargs)

    def product(self, *iterables, **kwargs):
        return self._wrap(it.product, *iterables, **kwargs)

    def permutations(self, r=None):
        return self._wrap(it.permutations, r)

    def combinations(self, r):
        return self._wrap(it.combinations, r)

    def combinations_with_replacement(self, r):
        return self._wrap(it.combinations_with_replacement, r)

    def _wrap(self, func, *args, **kwargs):
        return self.__class__(func(self._it, *args, **kwargs))

    def _wrap1(self, func, *args, **kwargs):
        return self.__class__(func(args[0], self._it, *args[1:], **kwargs))


class RichIteratorChain(object):

    def __init__(self, rich_iter):
        self._ri = rich_iter

    def __call__(self, *iterables):
        return self._ri._wrap(it.chain, *iterables)

    def from_iterable(self):
        return self._ri._wrap(it.chain.from_iterable)
