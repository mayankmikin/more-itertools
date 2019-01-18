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
    def swap(py3_name, py2_name):
        if hasattr(cls, py3_name):  # pragma: no cover
            setattr(cls, py2_name, getattr(cls, py3_name))
            delattr(cls, py3_name)

    if not six.PY3:  # pragma: no cover
        swap('__next__', 'next')
        swap('__bool__', '__nonzero__')
        swap('__truediv__', '__div__')
    return cls


def add_swapped_operators(cls):
    for name in 'add', 'mul', 'pow':
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

    def __or__(self, func):
        return self.map(func)

    def __and__(self, predicate):
        return self.filter(predicate)

    def __xor__(self, predicate):
        return self.filterfalse(predicate)

    def __rshift__(self, predicate):
        return self.dropwhile(predicate)

    def __lshift__(self, predicate):
        return self.takewhile(predicate)

    def __pow__(self, other):
        return (self.product(repeat=other) if isinstance(other, int) else
                self.product(other))

    def __mod__(self, r):
        return self.permutations(r)

    def __truediv__(self, r):
        return self.combinations(r)

    def __floordiv__(self, r):
        return self.combinations_with_replacement(r)

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

    def groupby(self, key=None, sort=False):
        iterable = sorted(self._it, key=key) if sort else self._it
        return self.__class__(it.groupby(iterable, key))

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

    def _wrap1(self, func, *args):
        return self.__class__(func(args[0], self._it, *args[1:]))


class RichIteratorChain(object):

    def __init__(self, rich_iter):
        self._ri = rich_iter

    def __call__(self, *iterables):
        return self._ri._wrap(it.chain, *iterables)

    def from_iterable(self):
        return self._ri._wrap(it.chain.from_iterable)
