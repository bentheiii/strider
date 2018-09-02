from typing import Callable, Iterable, Union, Dict

from textwrap import dedent
from functools import partial, update_wrapper
import re
import inspect

from strider.__util__ import *


class KeyCommand(Registry):
    """
    Commands bound to a key or keys
    """
    # A central dictionary mapping keys to their codes. If set, used to adjust the __doc__ of commands
    code_dict: Dict[str, int] = None

    def _update_doc(self):
        """
        updates the __doc__ of a command with the names of the keys bound to it.
        Codes that have no name in the code_dict are ignored.
        """
        self.__doc__ = dedent(self.__doc__).strip()
        if self.code_dict:
            keys = []
            codes = set(self.key_codes)
            # this seems pretty inefficient, but it's O(n^2) where n = number of key commands
            # doubling the number of commands currently: n=50, O(2500), doesn't even make a dent next to the stuff
            # opencv does
            for k, v in self.code_dict.items():
                if v in codes:
                    keys.append(pretty_key_name(k))
            # currently all key command docs are single-line, but let's future-proof
            if keys:
                self.__doc__ = ' or '.join(keys) + ': ' + self.__doc__

    def register_key(self):
        # NOTE: key command register_keys are not registered directly!!!
        return self.key_codes

    def register(self, key=...):
        if key is ...:
            key = self.register_key()
        for k in key:
            super().register(k)

    @classmethod
    def values_distinct(cls):
        # filters out repeating values
        prev = None
        for v in super().values():
            if prev is v:
                continue
            prev = v
            yield v

    def __init__(self, key_codes: Union[Iterable[int], int], func: Callable):
        if isinstance(key_codes, int):
            key_codes = (key_codes,)

        self.key_codes = key_codes
        update_wrapper(self, func)
        self._update_doc()
        self.__func__ = func
        super().__init__()
        self.allow_on_auto_play = False

    def __call__(self, *args, **kwargs):
        return self.__func__(*args, **kwargs)


def key_command(codes: Union[Iterable[int], int, str], **kwargs):
    """A KeyCommand wrapper to be used as a decorator"""
    def ret(func):
        kc = KeyCommand(codes, func)
        kc.__dict__.update(kwargs)
        return kc
    return ret


class SpecialCommand(Registry):
    """
    A special command parsed and called with parameters
    """
    _func_call_master_pattern = re.compile('(?P<name>[a-z0-9_]+)((?P<full>\s*\(.*\))|(?P<short>\s+[^(].*)|)\s*')

    @classmethod
    def parse_func_call(cls, line):
        """
        Parsing can occur in two ways:
        full: <func>(<arg0>, <arg1>...)- eval'ed and used as arguments
        short: <func> <arg0> <arg1>... - eval'ed as <func>("<arg0>", "<arg1>")
        min: <func> - run without arguments
        """
        m = cls._func_call_master_pattern.fullmatch(line)
        if not m:
            raise ValueError('could not parse line')
        if m['full']:
            arg_raw = m['full']
            if not arg_raw.endswith(',)'):
                arg_raw = m['full'][:-1] + ',)'  # add a comma to force the result to be a tuple
            args = eval(arg_raw, None, None)
        elif m['short']:
            args = [a for a in m['short'].split() if a]
        else:  # min
            args = ()
        comm = cls.get(m['name'])
        return comm, args

    def register_key(self):
        return self.__name__

    def __init__(self, func):
        update_wrapper(self, func)
        self.__func__ = func
        self.__doc__ = self.__name__ + str(inspect.signature(self.__func__)) + ': ' + self.__doc__
        super().__init__()

    def __call__(self, *args, **kwargs):
        return self.__func__(*args, **kwargs)
