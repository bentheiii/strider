from typing import Iterable, Union, Tuple, Mapping

QuickTagDict = Mapping[int, Tuple[str, str, Union['QuickTagDict', str, None]]]
# a QuickTagDict is a dict between an ascii key-code to a 3-tuple:
# [0]: the name of the key code (str)
# [1]: the name of the tag or option (str)
# [2]: the value to return if the option is chosen (str or None)
#       or another QuickTagDict as a sub-menu


def resolve_quick_tags(tags: Iterable[str], other_code=('.', ord('.')), none_code=('esc', 27)) \
        -> Tuple[QuickTagDict, int]:
    # although there is no enforcement of it, using the same tag twice is highly discouraged
    """
    :returns: the dict and the number of quicktags in total
    >>> assert resolve_quick_tags(['Vehicle','Person','2-Wheel-Vehicle']) == ({ord('v'):('v', 'Vehicle', 'Vehicle'),
    ...     ord('p'):('p', 'Person','Person'), ord('2'):('2', '2-Wheel-Vehicle','2-Wheel-Vehicle'),
    ...      27:('esc', '<cancel>', None)}, 3)
    >>> assert resolve_quick_tags(['hi','i','howdy','hii'], none_code=None) == ({ord('h'): ('h', 'hi','hi'),
    ...     ord('o'):('o', 'howdy', 'howdy'), ord('i'):('i', 'i','i'),
    ...     ord('.'):('.', '<more>', {ord('h'): ('h', 'hii','hii')})}, 4)
    """
    ret = {}
    num = 0
    others = []
    for tag in tags:
        tag = tag.strip()
        if not tag:  # skip blank tags
            continue

        has_alnum = False
        for c in tag.lower():
            if not c.isalnum():
                continue  # continue if not alnum
            has_alnum = True
            code = ord(c)
            if code in ret:
                continue
            ret[code] = (c, tag, tag)
            num += 1
            break
        else:  # we found no valid chars
            if not has_alnum:
                raise Exception('can\'t handle tag without alnum characters ' + tag)
            others.append(tag)

    if others:
        s, code = other_code
        other_resolved, o_num = resolve_quick_tags(others, other_code=other_code, none_code=none_code)
        ret[code] = (s, '<more>', other_resolved)
        num += o_num

    if none_code:
        s, code = none_code
        ret[code] = (s, '<cancel>', None)

    return ret, num


def tag_names(qt_dict: QuickTagDict):
    """
    assured:
    tag_names(resolve_quick_tags(<ITER>,...)) == set(<ITER>)
    >>> assert tag_names(resolve_quick_tags(['Vehicle','Person','2-Wheel-Vehicle'])[0]) == {'Vehicle','Person','2-Wheel-Vehicle'}
    >>> assert tag_names(resolve_quick_tags(['hi','i','hii'], none_code=None)[0]) == {'hi','i','hii'}
    """
    ret = set()
    if not qt_dict:
        return ret
    for _, _, v in qt_dict.values():
        if v is None:
            continue
        elif isinstance(v, Mapping):
            ret.update(tag_names(v))
        else:
            assert isinstance(v, str)
            ret.add(v)
    return ret
