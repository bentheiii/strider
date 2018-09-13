import importlib.util

from strider.merge_tracks.rules import Rule, rule

annotation_keyword = 'rule'


def load_rule_file(src_path):
    spec = importlib.util.spec_from_file_location("", src_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    rule_primitives = set()

    annotations = getattr(mod, '__annotation__', {})

    rule_primitives.update((k, v) for (k, v) in vars(mod).items()
                           if not k.startswith('_')
                           and (isinstance(v, Rule)) or annotations.get(k) == annotation_keyword)

    return [rule(v, name=k) for (k, v) in rule_primitives]
