from typing import Callable, Iterable, Union, Dict

from textwrap import dedent
from functools import partial, update_wrapper
import re
import inspect

from strider.__util__ import *


def clean_str(s):
    return dedent(' '.join(s.strip().split()))


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
        self.__doc__ = clean_str(self.__doc__)
        if self.code_dict:
            # this seems pretty inefficient, but it's O(n^2) where n = number of key commands
            # doubling the number of commands currently: n=50, O(2500), doesn't even make a dent next to the stuff
            # cv2 does
            for k, v in self.code_dict.items():
                if v == self.key_code:
                    self.__doc__ = pretty_key_name(k) + ': ' + self.__doc__
                    break

    def register_key(self):
        return self.key_code

    def __init__(self, key_code: int, func: Callable, *, allow_on_auto_play=False):
        self.key_code = key_code
        update_wrapper(self, func)
        self.__func__ = func
        self.allow_on_auto_play = allow_on_auto_play
        self._update_doc()

        super().__init__()

    def __call__(self, *args, **kwargs):
        return self.__func__(*args, **kwargs)


def key_command(codes: Union[Iterable[int], int, str], **kwargs):
    """A KeyCommand wrapper to be used as a decorator"""
    return partial(KeyCommand, codes, **kwargs)


class SpecialCommand(Registry):
    """
    A special command parsed and called with parameters
    """
    _func_call_master_pattern = re.compile('(?P<name>[a-z0-9_]+)((?P<full>\s*\(.*\))|(?P<short>\s+[^(].*)|)\s*')

    def _update_doc(self):
        self.__doc__ = self.__name__ + str(inspect.signature(self.__func__)) + ': ' + clean_str(self.__doc__)

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
        self._update_doc()

        super().__init__()

    def __call__(self, *args, **kwargs):
        return self.__func__(*args, **kwargs)
