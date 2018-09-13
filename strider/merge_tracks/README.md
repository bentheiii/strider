# Strider- Merge_Tracks

This is an advanced tool to ease merging and mutating strider track files.

## How To Use
`python -m strider.merge_tracks <destination file> <source files>`

This takes all the tracks present in the source files and merges them into the destination file and saves it.

In case of an ID conflict (two tracks from the different sources having the same ID), the program will roll a random new ID for one of the tracks. This behaviour can be changed with the `--on_conflict` flag.

Run with the `--help` flag to see all options.

## Rules and Advanced Usage
The program also takes a `-r <python file>` that lists custom rules to be applied to each track as it is merged. Example rule file:

```python
# rules have a trigger and an action
from strider.merge_tracks import trigger, action, rule

@trigger
def starts_at_0(track, source_pack, destination_pack):
    return track.points.keys()[0] == 0
@action
def clear_tags(track, source_pack, destination_pack):
    track.tags.clear()
    # if an action doesn't return anything, then the input track is treated as the return value 
    
# create a rule that clears all the tags in tracks that start at 0
rule_0 = rule(starts_at_0, clear_tags)
# equivalent
rule_0 = starts_at_0 >> clear_tags

# all variables in the module of the Rule type will be used as rules for merging.
# also, all variables that are annotated with the string 'rule'

# equivalent to the above, without importing anything
rule_0: 'rule' = (lambda track, *_: track.points.keys()[0] == 0, lambda track, *_: track.tags.clear())

# rules can also be done with a single declaration
@rule
def rule_0(track, *_):
    if track.points.keys()[0] == 0:
        track.tags.clear()
        return True  # single-declaration rules must explicitly return true or the new track if the rule is applied
    return False

# equivalent
rule_0 : 'rule'
def rule_0(track, *_):
    if track.points.keys()[0] == 0:
        track.tags.clear()
        return True
    return False

# if an action returns merge_tracks.SKIP or the string 'SKIP', the track is ignored
@trigger
def has_ignore_tag(track, *_):
    return 'ignore' in track.tags

# ignore all tracks that have the "ignore" tag
rule_1 = has_ignore_tag >> (lambda *a: 'SKIP')
# the module also has some useful builtin triggers and actions
from strider.merge_tracks import source_re, has_tag, add_tags, change_id
# skip all tracks with tag "queen" in source files with the name bees
rule_2 = (source_re('bees') & has_tag('queen')) >> 'SKIP'
# mark all tracks from files called ant or ants by adding a tag called 'ant' and adding an 'a' to the id
rule_3 = source_re('ants?') >> add_tags('ant').then(change_id(prefix='a_'))
```
Note that only the first rule that matches will be applied to each track. Actions can be chained using the `then` and `after` functions. 

Although rule files are the recommended way to add rules. It is also possible to add inline rules using the `-ir` argument. The following will add a rule that prepends all tracks with the 't' prefix:

`strider.merge_tracks <...> -ir True>>change_id(prefix='t')`