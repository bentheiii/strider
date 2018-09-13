from typing import Optional, Tuple, Pattern, Callable, Union

from abc import ABC, abstractmethod
from copy import copy
import functools
import os.path
import re

import strider
from strider.__util__ import *

SKIP = 'SKIP'


class Trigger:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.__func__ = func

    def __call__(self, track, pack):
        try:
            return self.__func__(track, pack)
        except TypeError:
            return self.__func__(track)

    def __and__(self, other):
        return type(self)(lambda *a, **k: self(*a, **k) and other(*a, **k))

    def __or__(self, other):
        return type(self)(lambda *a, **k: self(*a, **k) or other(*a, **k))

    def __xor__(self, other):
        return type(self)(lambda *a, **k: self(*a, **k) ^ other(*a, **k))

    def __invert__(self):
        return type(self)(lambda *a, **k: not self(*a, **k))

    def __rshift__(self, other):
        return rule(self, other)


@overload
def trigger(*args, **kwargs) -> Trigger:
    return Trigger(*args, **kwargs)


@trigger.register
def _(t: Trigger):
    return t


@trigger.register
def _(b: bool):
    return trigger(lambda x: b)


class Action:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.__func__ = func

    def __call__(self, track):
        ret = self.__func__(track)
        if ret is None:
            ret = track
        return ret

    def then(self, other):
        return type(self)(lambda x: other(self(x)))

    def after(self, other):
        return type(self)(lambda x: self(other(x)))

    def __rrshift__(self, other):
        return rule(other, self)


@overload
def action(*args, **kwargs) -> Action:
    return Action(*args, **kwargs)


@action.register
def _(a: Action):
    return a


@action.register
def _(a: str):
    if a == SKIP:
        return action(lambda *args: SKIP)
    raise ValueError(f'{a!r} not valid for action')


class Rule(ABC):
    def __init__(self, name: Optional[str] = None):
        self.name = name

    @abstractmethod
    def __call__(self, track: strider.Track, pack: strider.TrackPack) -> Tuple[bool, strider.Track]:
        pass


class ComboRule(Rule):
    def __init__(self, trigger_: Trigger, action_: Action, **kwargs):
        super().__init__(**kwargs)
        self.trigger = trigger(trigger_)
        self.action = action(action_)

    def __call__(self, track, pack):
        if self.trigger(track, pack):
            return True, self.action(track)
        else:
            return False, track


class FuncRule(Rule):
    def __init__(self, func, **kwargs):
        super().__init__(**kwargs)
        functools.update_wrapper(self, func)
        self.__func__ = func

    def __call__(self, track, pack):
        try:
            result = self.__func__(track, pack)
        except TypeError:
            result = self.__func__(track)

        if not result:
            return False, track

        if not isinstance(result, strider.Track):
            result = track
        return True, result


@overload
def rule(*args, **kwargs) -> Rule:
    return ComboRule(*args, **kwargs)


@rule.register
def _(func: object, **kwargs):
    return FuncRule(func, **kwargs)


@rule.register
def _(t: tuple, **kwargs):
    return rule(*t, **kwargs)


@rule.register
def _(r: Rule, name=None):
    if name is not None:
        r = copy(r)
        r.name = name
    return r


# region common
def source_re(r: Union[str, Pattern]):
    r = re.compile(r)

    @trigger
    def ret(t, p):
        return any(r.fullmatch(k) for k in (
            p.name,
            os.path.basename(p.name),
            os.path.splitext(os.path.basename(p.name))[0]
        ))

    return ret


def has_tag(t: str):
    @trigger
    def ret(track):
        return t in track.tags

    return ret


def add_tags(*tags):
    @action
    def ret(track):
        track.tags.update(tags)

    return ret


def change_id(*, prefix='', postfix=''):
    @action
    def ret(track):
        track.id = prefix + track.id + postfix

    return ret
# endregion
