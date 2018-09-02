from abc import ABC, abstractmethod


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
    def get(cls, item):
        return cls._registered[item]

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
    shift_* -> shift+*
    {direction} -> {direction} arrow
    """
    if n.startswith('shift_'):
        return 'shift+' + n[len('shift_'):]
    if n in ('left', 'right', 'up', 'down'):
        return n + ' arrow'
    return n


__all__ = ['Registry', 'pretty_key_name']
