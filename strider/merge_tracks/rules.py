from typing import Optional, Tuple, Pattern, Union

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

    def __call__(self, track, src_pack, dst_pack):
        return self.__func__(track, src_pack, dst_pack)

    def __and__(self, other):
        """
        get a trigger that is only triggered if both triggers are met
        """
        other = trigger(other)
        return trigger(lambda *a, **k: self(*a, **k) and other(*a, **k))

    def __or__(self, other):
        """
        get a trigger that is only triggered if either triggers are met
        """
        other = trigger(other)
        return trigger(lambda *a, **k: self(*a, **k) or other(*a, **k))

    def __xor__(self, other):
        """
        get a trigger that is only triggered if only one of triggers are met
        """
        other = trigger(other)
        return trigger(lambda *a, **k: self(*a, **k) ^ other(*a, **k))

    def __invert__(self):
        """
        get a trigger that is only triggered if this trigger is not met
        """
        return trigger(lambda *a, **k: not self(*a, **k))

    def __rshift__(self, other):
        """
        create a rule with other as the rule
        """
        return rule(self, other)


@overload
def trigger(*args, **kwargs) -> Trigger:
    """
    create a trigger, acceptable inputs:
    trigger(function)-> a trigger wrapping the function
    trigger(trigger)-> the same trigger
    trigger(bool)-> a trigger that always fails or passes
    """
    return Trigger(*args, **kwargs)


@trigger.register
def _(t: Trigger):
    return t


@trigger.register
def _(b: bool):
    return trigger(lambda *_: b)


class Action:
    def __init__(self, func):
        functools.update_wrapper(self, func)
        self.__func__ = func

    def __call__(self, track, src_pack, dst_pack):
        ret = self.__func__(track, src_pack, dst_pack)
        if ret is None:
            ret = track
        return ret

    def then(self, other):
        """
        activate another action after this one
        """
        other = action(other)
        return action(lambda *a: other(self(*a), *a[1:]))

    def after(self, other):
        """
        activate another action before this one
        """
        other = action(other)
        return other.then(self)

    def __rrshift__(self, other):
        """
        create a rule with other as the trigger
        """
        return rule(other, self)


@overload
def action(*args, **kwargs) -> Action:
    """
    create an action, acceptable inputs:
    action(function)-> a action wrapping the function
    action(action)-> the same action
    action('SKIP')-> an action that always returns 'SKIP'
    action(None)-> an action that doesn't change the track at all
    """
    return Action(*args, **kwargs)


@action.register
def _(a: Action):
    return a


@action.register
def _(a: str):
    if a == SKIP:
        return action(lambda *args: SKIP)
    raise ValueError(f'{a!r} not valid for action')


@action.register
def _(x: None):
    return action(lambda t, *_: t)


class Rule(ABC):
    def __init__(self, name: Optional[str] = None):
        self.name = name

    @abstractmethod
    def __call__(self, track: strider.Track, src_pack: strider.TrackPack, dst_pack: strider.TrackPack) -> Tuple[bool, strider.Track]:
        pass

    def __str__(self):
        return str(self.name)


class ComboRule(Rule):
    def __init__(self, trigger_: Trigger, action_: Action, **kwargs):
        super().__init__(**kwargs)
        self.trigger = trigger(trigger_)
        self.action = action(action_)

    def __call__(self, track, src_pack, dst_pack):
        if self.trigger(track, src_pack, dst_pack):
            return True, self.action(track, src_pack, dst_pack)
        else:
            return False, track


class FuncRule(Rule):
    def __init__(self, func, **kwargs):
        super().__init__(**kwargs)
        functools.update_wrapper(self, func)
        self.__func__ = func

    def __call__(self, track, src_pack, dst_pack):
        result = self.__func__(track, src_pack, dst_pack)

        if not result:
            return False, track

        if not isinstance(result, strider.Track):
            result = track
        return True, result


@overload
def rule(*args, **kwargs) -> Rule:
    """
    create an rule, acceptable inputs:
    rule(trigger, action)-> a rule activating the action if the trigger passes
    rule(function)-> a rule wrapping the function
    rule(rule)-> the same rule
    rule(tuple)->rule(*tuple)
    """
    return ComboRule(*args, **kwargs)


@rule.register
def _(func, **kwargs):
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
    """
    Creates a trigger that only passes if the source file path matches the regex pattern provided.
    Will pass if the pattern fully matches either the full path, the file name, or the file name without extension
    """
    r = re.compile(r)

    @trigger
    def ret(t, p, d):
        return any(r.fullmatch(k) for k in (
            p.name,
            os.path.basename(p.name),
            os.path.splitext(os.path.basename(p.name))[0]
        ))

    return ret


def has_tag(*tags: str):
    """
    Creates a trigger that only passes if the track has any of the tags in the arguments
    """

    @trigger
    def ret(track, p, d):
        return any(t in track.tags for t in tags)

    return ret


def add_tags(*tags):
    """
    Create an action that adds tags to the track
    """

    @action
    def ret(track, p, d):
        track.tags.update(tags)

    return ret


def change_id(*, prefix='', postfix=''):
    """
    Create an action that adds a prefix and postfix to the track's id
    """

    @action
    def ret(track, p ,d):
        track.id = prefix + track.id + postfix

    return ret


default = rule(True, None, name='default')
# endregion
