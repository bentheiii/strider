import importlib.util

import strider.merge_tracks.rules as rules
from strider.merge_tracks.rules import Rule, rule

annotation_keyword = 'rule'
annotation_keyword_no_convert = '__rule'
annotation_keyword_multi = 'rules'
annotation_keyword_multi_no_convert = '__rules'

def load_rule_file(src_path):
    spec = importlib.util.spec_from_file_location("", src_path)
    if not spec:
        raise ImportError
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    ret = []

    annotations = getattr(mod, '__annotation__', {})

    # get all public values in the module that are either of Rule type or have 'rule' annotations
    for (k, v) in vars(mod).items():
        if k.startswith('_'):
            continue  # skip non-public members
        annotation = annotations.get(k)
        if isinstance(v, Rule) or annotation == annotation_keyword:
            r = rule(v, name=k)
            ret.append(r)
        elif annotation == annotation_keyword_no_convert:
            ret.append(v)
        elif annotation == annotation_keyword_multi:
            r = (rule(s, name=k+'['+str(i)+']') for (i, s) in enumerate(v))
            ret.extend(r)
        elif annotation == annotation_keyword_multi_no_convert:
            ret.extend(v)
        else:
            pass

    # the name of a rule is the name of the variable
    return ret


def load_inline_rule(line):
    return eval(line, {}, rules.__dict__)
