import itertools as it
import functools
import operator

import six
from six.moves import filter, filterfalse, map, zip, zip_longest
try:
    accumulate = it.accumulate
except AttributeError:  # pragma: no cover
    from .recipes import accumulate


__all__ = ['RichIterator']


def make_py2_compatible(cls):
    if not six.PY3:  # pragma: no cover
        if hasattr(cls, '__next__'):
            cls.next = cls.__next__
            del cls.__next__
        if hasattr(cls, '__bool__'):
            cls.__nonzero__ = cls.__bool__
            del cls.__bool__
    return cls


def add_swapped_operators(cls):
    for name in 'add', 'mul':
        method = getattr(cls, '__{}__'.format(name), None)
        if method:
            add_swapped_method(cls, name, method)
    return cls


def add_swapped_method(cls, name, method):
    @functools.wraps(method)
    def swapped(self, other):
        if not isinstance(other, cls):
            other = cls(other)
        return method(other, self)

    swapped_name = '__r{}__'.format(name)
    swapped.__name__ = swapped_name
    if hasattr(swapped, '__qualname__'):  # pragma: no cover
        swapped.__qualname__ = swapped.__qualname__.replace(name, 'r' + name)
    setattr(cls, swapped_name, swapped)


@add_swapped_operators
@make_py2_compatible
class RichIterator(object):
    """Iterable wrapper exposing several convenience methods and operators."""

    __slots__ = ('_it',)

    def __init__(self, iterable):
        self._it = iter(iterable)

    def __iter__(self):
        return self

    def __next__(self):
        return next(self._it)

    def __bool__(self):
        try:
            next(self._it)
        except StopIteration:
            return False
        else:
            return True

    def __getitem__(self, index):
        if isinstance(index, int):
            try:
                return next(it.islice(self._it, index, None))
            except StopIteration:
                raise IndexError('index out of range')
        return self._wrap(it.islice, index.start, index.stop, index.step)

    def __copy__(self):
        self._it, new_it = it.tee(self._it)
        return self.__class__(new_it)

    def __add__(self, other):
        return self.chain(other)

    def __mul__(self, other):
        return self.zip(other)

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
        return tuple(self.__class__(i) for i in it.tee(self._it, n))

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
