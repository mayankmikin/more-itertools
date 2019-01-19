import itertools as it
import operator

import six
from six.moves import filter, filterfalse, map, zip, zip_longest
try:
    accumulate = it.accumulate
except AttributeError:  # pragma: no cover
    from .recipes import accumulate


__all__ = ['rich_iter']


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


@make_py2_compatible
class RichIterator(object):
    """Iterable wrapper exposing several convenience methods and operators."""

    __slots__ = ('_it', '_state_policy', '_wrap')

    def __init__(self, iterable, state_policy):
        self._it = iter(iterable)
        self.state_policy = state_policy

    @property
    def state_policy(self):
        return self._state_policy

    @state_policy.setter
    def state_policy(self, value):
        try:
            self._state_policy = value
            self._wrap = getattr(self, '_wrap_{}'.format(value))
        except AttributeError:
            raise ValueError('Invalid state_policy {!r}'.format(value))

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
        return self._wrap(it.islice, self._it,
                          index.start, index.stop, index.step)

    def __copy__(self):
        self._it, new_it = it.tee(self._it)
        return self.__class__(new_it, self._state_policy)

    def __add__(self, other):
        return self.chain(other)

    def __radd__(self, other):
        return self.__class__(other, self._state_policy).chain(self)

    def __mul__(self, other):
        return self.zip(other)

    def __rmul__(self, other):
        return self.__class__(other, self._state_policy).zip(self)

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

    def __rpow__(self, other):
        return self.__class__(other, self._state_policy).product(self)

    def __mod__(self, r):
        return self.permutations(r)

    def __truediv__(self, r):
        return self.combinations(r)

    def __floordiv__(self, r):
        return self.combinations_with_replacement(r)

    def cycle(self):
        return self._wrap(it.cycle, self._it)

    def accumulate(self, func=operator.add):
        return self._wrap(accumulate, self._it, func)

    @property
    def chain(self):
        return RichIteratorChain(self)

    def compress(self, selectors):
        return self._wrap(it.compress, self._it, selectors)

    def dropwhile(self, predicate):
        return self._wrap(it.dropwhile, predicate, self._it)

    def filter(self, predicate):
        return self._wrap(filter, predicate, self._it)

    def filterfalse(self, predicate):
        return self._wrap(filterfalse, predicate, self._it)

    def groupby(self, key=None, sort=False):
        iterable = sorted(self._it, key=key) if sort else self._it
        return self._wrap(it.groupby, iterable, key)

    def map(self, func, *iterables):
        return self._wrap(map, func, self._it, *iterables)

    def starmap(self, func):
        return self._wrap(it.starmap, func, self._it)

    def takewhile(self, predicate):
        return self._wrap(it.takewhile, predicate, self._it)

    def tee(self, n=2):
        return tuple(self.__class__(iterator, self._state_policy)
                     for iterator in it.tee(self._it, n))

    def zip(self, *iterables):
        return self._wrap(zip, self._it, *iterables)

    def zip_longest(self, *iterables, **kwargs):
        return self._wrap(zip_longest, self._it, *iterables, **kwargs)

    def product(self, *iterables, **kwargs):
        return self._wrap(it.product, self._it, *iterables, **kwargs)

    def permutations(self, r=None):
        return self._wrap(it.permutations, self._it, r)

    def combinations(self, r):
        return self._wrap(it.combinations, self._it, r)

    def combinations_with_replacement(self, r):
        return self._wrap(it.combinations_with_replacement, self._it, r)

    def _wrap_shared(self, func, *args, **kwargs):
        return self.__class__(func(*args, **kwargs), self._state_policy)

    def _wrap_exclusive(self, func, *args, **kwargs):
        self._it = RuntimeErrorIterator
        return self.__class__(func(*args, **kwargs), self._state_policy)

    def _wrap_mutable(self, func, *args, **kwargs):
        self._it = func(*args, **kwargs)
        return self

    def _wrap_immutable(self, func, *args, **kwargs):
        _it = self._it
        _it_idx = 0 if args[0] is _it else 1 if args[1] is _it else None
        if _it_idx is not None:
            self._it, new_it = it.tee(_it)
            args = list(args)
            args[_it_idx] = new_it
        return self.__class__(func(*args, **kwargs), self._state_policy)


class RichIteratorChain(object):

    __slots__ = ('_ri',)

    def __init__(self, rich_iterator):
        self._ri = rich_iterator

    def __call__(self, *iterables):
        return self._ri._wrap(it.chain, self._ri._it, *iterables)

    def from_iterable(self):
        return self._ri._wrap(it.chain.from_iterable, self._ri._it)


@make_py2_compatible
class RewindableRichIterator(RichIterator):

    __slots__ = RichIterator.__slots__ + ('_arg', '_seen', '_next')

    def __init__(self, iterable, state_policy):
        super(RewindableRichIterator, self).__init__(iterable, state_policy)
        super_self = super(RewindableRichIterator, self)
        super_next = super_self.__next__ if six.PY3 else super_self.next
        if self._it is iterable:
            self._arg = None
            self._seen = []

            def _next(super_next=super_next, append=self._seen.append):
                value = super_next()
                append(value)
                return value
            self._next = _next
        else:
            self._arg = iterable
            self._seen = None
            self._next = super_next

    def __next__(self):
        return self._next()

    def rewind(self):
        if self._it is RuntimeErrorIterator:
            raise RuntimeError('iterator can no longer be used')
        if self._seen is None:
            self._it = iter(self._arg)
        else:
            self._it = it.chain(self._seen[:], self._it)
            del self._seen[:]
        return self


@make_py2_compatible
class RuntimeErrorIterator:

    def __iter__(self):
        raise RuntimeError('iterator can no longer be used')

    def __next__(self):
        raise RuntimeError('iterator can no longer be used')


RuntimeErrorIterator = RuntimeErrorIterator()


class rich_iter(object):

    def __new__(cls, iterable, rewindable=False, state_policy='shared'):
        cls = RewindableRichIterator if rewindable else RichIterator
        return cls(iterable, state_policy)

    @classmethod
    def count(cls, start=0, step=1, rewindable=False, state_policy='shared'):
        return cls(it.count(start, step), rewindable, state_policy)

    @classmethod
    def repeat(cls, obj, times=None, rewindable=False, state_policy='shared'):
        return cls(it.repeat(obj, times) if times is not None else
                   it.repeat(obj), rewindable, state_policy)
