from typing import Callable, Iterable, Union, Dict, Optional

import re
import inspect
from string import Formatter
from textwrap import dedent
from functools import partial, update_wrapper

from strider.cv_codes import Codes, code_keys
from strider.__util__ import *


def clean_str(s):
    return dedent(' '.join(s.strip().split()))


class CountedItem(int):
    def __format__(self, format_spec:str):
        ind = format_spec.find('/')
        if ind >= 0:
            single, plural = format_spec[:ind], format_spec[ind+1:]
        else:
            single, plural = format_spec, format_spec+'s'
        return str(self) + ' ' + (plural if self > 1 else single)


class PluralFormatter(Formatter):
    def convert_field(self, value, conversion):
        if conversion == 'n':
            return CountedItem(value)
        return super().convert_field(value, conversion)


class KeyCommand(Registry):
    """
    Commands bound to a key or keys
    """
    # A central dictionary mapping codes to their keys. If set, used to adjust the __doc__ of commands
    code_dict: Dict[int, str] = {}
    plural_formatter = PluralFormatter()

    def _update_doc(self, doc_placeholders: Optional[Iterable]):
        """
        updates the __doc__ of a command with the names of the keys bound to it.
        Codes that have no name in the code_dict are ignored.
        """
        if doc_placeholders:
            self.__doc__ = self.plural_formatter.format(self.__doc__, *(str(x) for x in doc_placeholders))
        self.__doc__ = clean_str(self.__doc__)
        if self.key_code in self.code_dict:
            self.__doc__ = pretty_key_name(self.code_dict[self.key_code]) + ': ' + self.__doc__

    def register_key(self):
        return self.key_code

    def __init__(self, key_code: int, func: Callable, *,
                 allow_on_auto_play=False, doc_placeholders: Optional[Iterable] = None):
        self.key_code = key_code
        update_wrapper(self, func)
        self.__func__ = func
        self.allow_on_auto_play = allow_on_auto_play
        self._update_doc(doc_placeholders)

        super().__init__()

    def __call__(self, *args, **kwargs):
        return self.__func__(*args, **kwargs)

    @classmethod
    def import_codes(cls, codes: Codes):
        for k in code_keys:
            v = getattr(codes, k)
            if not isinstance(v, int):
                raise TypeError(f'key {k} has non-int value {v}')
            if cls.code_dict.setdefault(v, k) != k:
                raise ValueError(f'multiple values for code {v}')


def key_command(codes: Union[Iterable[int], int, str], **kwargs):
    """A KeyCommand wrapper to be used as a decorator"""
    return partial(KeyCommand, codes, **kwargs)


class SpecialCommand(Registry):
    """
    A special command parsed and called with parameters
    """
    _func_call_master_pattern = re.compile(r'(?P<name>[a-z0-9_]+)((?P<full>\s*\(.*\))|(?P<short>\s+[^(].*)|)\s*')

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
