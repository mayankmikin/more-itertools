import abc
import itertools as it
import functools
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


def add_swapped_operators(cls):
    for name in 'add', 'mul', 'pow':
        add_swapped_method(cls, name)
    return cls


def add_swapped_method(cls, name):
    method_name = '__{}__'.format(name)
    rmethod_name = '__r{}__'.format(name)

    @functools.wraps(getattr(cls, method_name))
    def rmethod(self, other):
        if not isinstance(other, cls):
            other = self.__class__(other)
        return getattr(other, method_name)(self)

    rmethod.__name__ = rmethod_name
    if hasattr(rmethod, '__qualname__'):  # pragma: no cover
        rmethod.__qualname__ = rmethod.__qualname__.replace(name, 'r' + name)
    setattr(cls, rmethod_name, rmethod)


@add_swapped_operators
@make_py2_compatible
@six.add_metaclass(abc.ABCMeta)
class AbstractRichIterator(object):
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
        return self._wrap0(it.islice, index.start, index.stop, index.step)

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

    def cycle(self):
        return self._wrap0(it.cycle)

    def accumulate(self, func=operator.add):
        return self._wrap0(accumulate, func)

    @property
    def chain(self):
        return RichIteratorChain(self)

    def compress(self, selectors):
        return self._wrap0(it.compress, selectors)

    def dropwhile(self, predicate):
        return self._wrap1(it.dropwhile, predicate)

    def filter(self, predicate):
        return self._wrap1(filter, predicate)

    def filterfalse(self, predicate):
        return self._wrap1(filterfalse, predicate)

    def groupby(self, key=None, sort=False):
        iterable = sorted(self._it, key=key) if sort else self._it
        return self._from_iterator(it.groupby(iterable, key))

    def map(self, func, *iterables):
        return self._wrap1(map, func, *iterables)

    def starmap(self, func):
        return self._wrap1(it.starmap, func)

    def takewhile(self, predicate):
        return self._wrap1(it.takewhile, predicate)

    def tee(self, n=2):
        return tuple(self.__class__(i) for i in it.tee(self._it, n))

    def zip(self, *iterables):
        return self._wrap0(zip, *iterables)

    def zip_longest(self, *iterables, **kwargs):
        return self._wrap0(zip_longest, *iterables, **kwargs)

    def product(self, *iterables, **kwargs):
        return self._wrap0(it.product, *iterables, **kwargs)

    def permutations(self, r=None):
        return self._wrap0(it.permutations, r)

    def combinations(self, r):
        return self._wrap0(it.combinations, r)

    def combinations_with_replacement(self, r):
        return self._wrap0(it.combinations_with_replacement, r)

    def _wrap0(self, func, *args, **kwargs):
        return self._from_iterator(func(self._it, *args, **kwargs))

    def _wrap1(self, func, *args):
        return self._from_iterator(func(args[0], self._it, *args[1:]))

    @abc.abstractmethod
    def _from_iterator(self, iterator):
        """Return a rich iterator from the given ``iterator``"""


class RichIteratorChain(object):

    __slots__ = ('_ri',)

    def __init__(self, rich_iter):
        self._ri = rich_iter

    def __call__(self, *iterables):
        return self._ri._wrap0(it.chain, *iterables)

    def from_iterable(self):
        return self._ri._wrap0(it.chain.from_iterable)


@make_py2_compatible
class RewindableRichIterator(AbstractRichIterator):

    __slots__ = AbstractRichIterator.__slots__ + ('_arg', '_seen', '_next')

    def __init__(self, iterable):
        super(RewindableRichIterator, self).__init__(iterable)
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
        if self._seen is None:
            self._it = iter(self._arg)
        else:
            self._it = it.chain(self._seen[:], self._it)
            del self._seen[:]
        return self


class SharedRichIteratorMixin(object):

    __slots__ = ()

    def _from_iterator(self, iterator):
        return self.__class__(iterator)


class MutableRichIteratorMixin(object):

    __slots__ = ()

    def _from_iterator(self, iterator):
        self._it = iterator
        return self


class ExclusiveRichIteratorMixin(object):

    __slots__ = ()

    def _from_iterator(self, iterator):
        self._it = RuntimeErrorIterator
        return self.__class__(iterator)


class ExclusiveRewindableRichIterator(ExclusiveRichIteratorMixin,
                                      RewindableRichIterator):

    __slots__ = ()

    def rewind(self):
        if self._it is RuntimeErrorIterator:
            raise RuntimeError('iterator can no longer be used')
        return super(ExclusiveRewindableRichIterator, self).rewind()


@make_py2_compatible
class RuntimeErrorIterator:

    def __iter__(self):
        raise RuntimeError('iterator can no longer be used')

    def __next__(self):
        raise RuntimeError('iterator can no longer be used')


RuntimeErrorIterator = RuntimeErrorIterator()


def register_rich_iterator(name, state, rewindable):
    bases = (
        SharedRichIteratorMixin if state == 'shared' else
        MutableRichIteratorMixin if state == 'mutable' else
        ExclusiveRichIteratorMixin if state == 'exclusive' else None,
        RewindableRichIterator if rewindable else AbstractRichIterator
    )
    attrs = {'__module__': __name__, '__slots__': ()}
    REGISTRY[state, rewindable] = type(name, bases, attrs)


REGISTRY = {}
register_rich_iterator('SharedRichIterator', 'shared', False)
register_rich_iterator('SharedRewindableRichIterator', 'shared', True)
register_rich_iterator('MutableRichIterator', 'mutable', False)
register_rich_iterator('MutableRewindableRichIterator', 'mutable', True)
register_rich_iterator('ExclusiveRichIterator', 'exclusive', False)
REGISTRY['exclusive', True] = ExclusiveRewindableRichIterator


class rich_iter(object):

    def __new__(cls, iterable, rewindable=False, state='shared'):
        try:
            return REGISTRY[state, rewindable](iterable)
        except KeyError:
            raise ValueError('Invalid state {!r}'.format(state))

    @classmethod
    def count(cls, start=0, step=1, rewindable=False, state='shared'):
        return cls(it.count(start, step), rewindable=rewindable, state=state)

    @classmethod
    def repeat(cls, object, times=None, rewindable=False, state='shared'):
        return cls(it.repeat(object, times) if times is not None else
                   it.repeat(object), rewindable=rewindable, state=state)
