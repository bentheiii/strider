from typing import Union, Iterable, Tuple, MutableMapping, Optional

import random
import json
from math import ceil

from strider.track import Track
from strider.__data__ import __version__


class TrackPack:
    def __init__(self, name=None, video_path=None):
        # enabled_tracks is a subset of tracks
        # by default, all tracks are disabled, use enable_all to enable all track at once
        self._enabled_tracks: MutableMapping[str, Track] = {}
        self.tracks: MutableMapping[str, Track] = {}
        self.name: Optional[str] = name
        self.video_path: Optional[str] = video_path

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.tracks[item]
        if isinstance(item, Track):
            return item
        raise TypeError

    def all_tags(self):
        ret = set()
        for t in self.tracks.values():
            ret.update(t.tags)
        return ret

    def has_tag(self, tag):
        for t in self.tracks.values():
            if t in t.tags:
                return True
        return False

    def to_dict(self):
        d = {
            'strider_version': __version__,
            'video_path': self.video_path,
            'tracks': [x.to_dict() for x in self.tracks.values()]
        }
        return d

    @classmethod
    def from_dict(cls, d, **kwargs):
        for key in ('video_path', 'name'):
            if key in kwargs:
                continue
            if key not in d:
                continue
            kwargs[key] = d[key]

        ret = cls(**kwargs)
        for t in d.get('tracks', ()):
            track = Track.from_dict(t)
            ret.tracks[track.id] = track
        return ret

    def write(self, dst):
        json.dump(self.to_dict(), dst, indent=1)

    @classmethod
    def read(cls, src, **kwargs):
        return cls.from_dict(json.load(src), **kwargs)

    def enable_track(self, track_or_id: Union[Track, str]):
        track_or_id = Track.id(track_or_id)

        if track_or_id in self._enabled_tracks:
            return

        self._enabled_tracks[track_or_id] = self.tracks[track_or_id]

    def disable_track(self, track_or_id: Union[Track, str]):
        track_or_id = Track.id(track_or_id)

        if track_or_id not in self._enabled_tracks:
            return

        del self._enabled_tracks[track_or_id]

    def toggle_track(self, track_or_id: Union[Track, str]):
        track_or_id = Track.id(track_or_id)

        if track_or_id in self._enabled_tracks:
            self.disable_track(track_or_id)
        else:
            self.enable_track(track_or_id)

    def enable_all(self):
        self._enabled_tracks.update(self.tracks)

    def disable_all(self):
        self._enabled_tracks.clear()

    def is_enabled(self, track_or_id: Union[Track, str]):
        track_or_id = Track.id(track_or_id)

        return track_or_id in self._enabled_tracks

    def under(self, frame) -> Iterable[Tuple[Track, Iterable[Tuple[int, Tuple[int, int]]]]]:
        for t in self._enabled_tracks.values():
            yield t, t.under(frame)

    def new_id(self, max_coff=2.0):
        # O(max_coff / (max_coff-1))
        max_id = ceil(len(self.tracks) * max_coff)
        while True:
            ret = str(random.randint(0, max_id))
            if ret not in self.tracks:
                return ret

    def add_track(self, track):
        self.tracks[track.id] = track

    def delete_track(self, tid):
        tid = Track.id(tid)
        ret = self[tid]

        if tid in self._enabled_tracks:
            del self._enabled_tracks[tid]
        del self.tracks[tid]

        return ret

    def disabled(self):
        for t in self.tracks.values():
            if t.id not in self._enabled_tracks:
                yield t

    def enabled(self):
        yield from self._enabled_tracks.values()
