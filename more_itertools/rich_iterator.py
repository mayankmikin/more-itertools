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

    def rewind(self):
        raise NotImplementedError('rewind is not supported for this iterator')

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


class RewindableRichIterable(AbstractRichIterator):

    __slots__ = AbstractRichIterator.__slots__ + ('_iterable',)

    def __init__(self, iterable):
        self._iterable = iterable
        super(RewindableRichIterable, self).__init__(iterable)

    def rewind(self):
        self._it = iter(self._iterable)
        return self


@make_py2_compatible
class RewindableRichIterator(AbstractRichIterator):

    __slots__ = AbstractRichIterator.__slots__ + ('_seen',)

    def __init__(self, iterable):
        self._seen = []
        super(RewindableRichIterator, self).__init__(iterable)

    def __next__(self):
        value = next(self._it)
        self._seen.append(value)
        return value

    def rewind(self):
        self._it = it.chain(self._seen[:], self._it)
        del self._seen[:]
        return self


class SharedRichIteratorMixin(object):

    def _from_iterator(self, iterator):
        return self.__class__(iterator)


class MutableRichIteratorMixin(object):

    def _from_iterator(self, iterator):
        self._it = iterator
        return self


class ExclusiveRichIteratorMixin(object):

    def _from_iterator(self, iterator):
        self._it = RuntimeErrorIterator()
        return self.__class__(iterator)


class ExclusiveRewindableRichIterable(RewindableRichIterable):

    def _from_iterator(self, iterator):
        self.rewind()
        return self.__class__(iterator)


class ExclusiveRewindableRichIterator(ExclusiveRichIteratorMixin,
                                      RewindableRichIterator):

    def rewind(self):
        if isinstance(self._it, RuntimeErrorIterator):
            raise RuntimeError('iterator can no longer be used')
        return super(ExclusiveRewindableRichIterator, self).rewind()


@make_py2_compatible
class RuntimeErrorIterator:

    def __iter__(self):
        return self

    def __next__(self):
        raise RuntimeError('iterator can no longer be used')


def register_rich_iterator(name, state, is_rewindable=False, is_iterator=None):
    bases = []
    if state == 'shared':
        bases.append(SharedRichIteratorMixin)
    elif state == 'mutable':
        bases.append(MutableRichIteratorMixin)
    elif state == 'exclusive':
        bases.append(ExclusiveRichIteratorMixin)

    if is_rewindable:
        key = (state, is_iterator)
        if is_iterator:
            bases.append(RewindableRichIterator)
        else:
            bases.append(RewindableRichIterable)
    else:
        key = state
        bases.append(AbstractRichIterator)
    REGISTRY[key] = type(name, tuple(bases), {'__module__': __name__})


REGISTRY = {}
register_rich_iterator('SharedRichIterator', 'shared')
register_rich_iterator('SharedRewindableRichIterator', 'shared', True, True)
register_rich_iterator('SharedRewindableRichIterable', 'shared', True, False)
register_rich_iterator('MutableRichIterator', 'mutable')
register_rich_iterator('MutableRewindableRichIterator', 'mutable', True, True)
register_rich_iterator('MutableRewindableRichIterable', 'mutable', True, False)
register_rich_iterator('ExclusiveRichIterator', 'exclusive')
REGISTRY['exclusive', True] = ExclusiveRewindableRichIterator
REGISTRY['exclusive', False] = ExclusiveRewindableRichIterable


class rich_iter(object):

    def __new__(cls, iterable, rewindable=False, state='shared'):
        if not rewindable:
            factory = REGISTRY[state]
        else:
            is_iterator = iter(iterable) is iterable
            factory = REGISTRY[state, is_iterator]
        return factory(iterable)

    @classmethod
    def count(cls, start=0, step=1, rewindable=False, state='shared'):
        return cls(it.count(start, step), rewindable=rewindable, state=state)

    @classmethod
    def repeat(cls, object, times=None, rewindable=False, state='shared'):
        return cls(it.repeat(object, times) if times is not None else
                   it.repeat(object), rewindable=rewindable, state=state)
