from abc import ABC, abstractmethod
from inspect import signature
import functools

class Registry(ABC):
    """
    An ABC for creating a class that keeps track of all its instances via a dict.
    Each subclass receives a different dictionary. Subclass this class this class with dict_cls=None
    to inherit parent's dictionary.
    """
    _registered: dict  # virtual member, a different dictionary is made for each subclass.

    def __init_subclass__(cls, dict_cls=dict, **kwargs):
        super().__init_subclass__(**kwargs)
        if dict_cls:
            cls._registered = dict_cls()

    @abstractmethod
    def register_key(self):
        pass

    def register(self, key=...):
        if key is ...:
            key = self.register_key()
        exist = self._registered.setdefault(key, self)
        if exist is not self:
            raise KeyError('the same key used twice: ' + str(key))

    def __init__(self):
        super().__init__()
        self.register()

    @classmethod
    def get(cls, item, default=None):
        return cls._registered.get(item, default)

    @classmethod
    def values(cls):
        return cls._registered.values()

    @classmethod
    def keys(cls):
        return cls._registered.keys()

    @classmethod
    def items(cls):
        return cls._registered.items()


def pretty_key_name(n: str):
    """
    Attempts to prettify key names.
    capital <x>-> shift+<x>
    shift_* -> shift+*
    {direction} -> {direction} arrow
    """
    if len(n) == 1 and n.isupper():
        return 'shift+' + n.lower()
    if n.startswith('shift_'):
        return 'shift+' + n[len('shift_'):]
    if n in ('left', 'right', 'up', 'down'):
        return n + ' arrow'
    return n


def ts_to_str(hour, minute, second, ms):
    s = format(second, '02') + format(ms, '.3g')[1:]
    if hour > 0:
        return f'{hour}:{minute:02}:{s}'
    return f'{minute:02}:{s}'


class Candidate:
    @staticmethod
    def _match_annotation(o, annot):
        try:
            return isinstance(o, annot)
        except TypeError:
            pass
        if callable(annot):
            return annot(o)
        raise TypeError(f"can't handle annotation {annot}")

    def __init__(self, func):
        try:
            sign = signature(func)
        except TypeError:
            sign = None
        self.sign = sign
        self.annot = getattr(func, '__annotations__', {})
        self.func = func

    def match(self, args, kwargs):
        if not self.sign:
            return True
        try:
            bound = self.sign.bind(*args, **kwargs)
        except TypeError:
            return False
        if self.annot:
            for argname, argv in bound.arguments.items():
                if not self._match_annotation(argv, self.annot.get(argname, object)):
                    return False
        return True


class overload:
    def __init__(self, func):
        self.candidates = [Candidate(func)]
        functools.update_wrapper(self, func)

    def register(self, func):
        self.candidates.append(Candidate(func))
        if func.__name__ == self.__name__:
            return self
        return func

    def dispatch(self, *args, **kwargs):
        return next((c for c in reversed(self.candidates)
                    if c.match(args, kwargs)), None)

    def __call__(self, *args, **kwargs):
        d = self.dispatch(*args, **kwargs)
        if not d:
            raise TypeError('bad arguments')
        return d.func(*args, **kwargs)


__all__ = ['Registry', 'pretty_key_name', 'ts_to_str', 'overload']
