import argparse
import warnings
from enum import Enum, auto

import strider
from strider.merge_tracks import load_rule_file, SKIP


class OnConflict(Enum):
    random = auto()
    prompt = auto()
    error = auto()


parser = argparse.ArgumentParser('strider.merge_tracks', fromfile_prefix_chars='@',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('dst', action='store', help='the destination file')
parser.add_argument('sources', action='store', nargs='+', help='the source files to merge')
parser.add_argument('-r', action='append', dest='rule_paths'
                    , help='add a python file with special rules for merging')

parser.add_argument('--on_conflict', action='store', default=OnConflict.random,
                    help='how to behave when an id conflict occurs', type=OnConflict.__getitem__, dest='on_conflict')
parser.add_argument('--silent_rules', action='store_true', default=False, dest='silent_rules',
                    help='if set, all rules will not print anything when triggered')


def main(args=None):
    args = parser.parse_args(args)
    rules = []
    if args.rule_paths:
        for p in args.rule_paths:
            to_add = load_rule_file(p)
            if not to_add:
                warnings.warn('no rules detected in file ' + p)
            else:
                print(f'{len(to_add)} rules in {p}')
            rules.extend(to_add)
        if len(args.rule_paths) > 1:
            print(f'{len(rules)} rules total')

    def apply_rules(track, pack):
        for rule in rules:
            changed, track = rule(track, pack)
            if changed:
                if not args.silent_rules:
                    print(f'{track} @ {pack.name}: Rule {rule.name}')
                break
        return track

    dst = strider.TrackPack()
    dst.name = dst

    def handle_conflict(track):
        if args.on_conflict == OnConflict.error:
            raise Exception(f'ID conflict: track with id {track.id} already exists in destination')
        elif args.on_conflict == OnConflict.prompt:
            new_id = input(f'track with id {track.id} already exists in destination,'
                           f' enter a new id (leave blank for auto):\n')
            track.id = new_id or dst.new_id()
        elif args.on_conflict == OnConflict.random:
            new_id = dst.new_id()
            print(f'track with id {track.id} already exists in destination, new_id: {new_id}')
            track.id = new_id
        else:
            assert False

    for src_path in args.sources:
        with open(src_path) as r:
            src = strider.TrackPack.read(r)
            src.name = src_path
        for track in src.tracks.values():
            track = apply_rules(track, src)
            if track == SKIP:
                continue
            while track.id in dst.tracks:  # in case of OnConflict.prompt, its possible to have two conflicts in a row
                handle_conflict(track)
            dst.add_track(track)

    with open(args.dst, 'w') as w:
        dst.write(w)

    print(f'merged {len(args.sources)} track packs (total {len(dst.tracks)} tracks)')


if __name__ == '__main__':
    main()
