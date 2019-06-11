from typing import Tuple, Set, Optional

from sortedcontainers import SortedDict


class PointOverrideException(Exception):
    pass


class Track:
    @staticmethod
    def id(t):
        """
        Try to parse an object as a Track id
        """
        if isinstance(t, int):
            return str(t)
        if isinstance(t, str):
            return t
        return t.id

    def __init__(self):
        self.id: str = None
        self.points = SortedDict()
        self.color: Tuple[int, int, int] = None
        self.tags: Set[str] = set()

    def to_dict(self):
        ret = {
            'id': self.id,
            'color': self.color,
            'tags': list(self.tags),

            # keep points last for easier manual editing
            'points': list(self.points.items()),
        }
        return ret

    @classmethod
    def from_dict(cls, d):
        ret = cls()
        ret.id = d['id']
        ret.color = tuple(d['color'])
        ret.tags.update(x.lower() for x in d.get('tags', ()))

        ret.points.update(d['points'])
        return ret

    def under(self, frame):
        """
        Get all points that occur before (exclusive) the frame
        """
        keys = self.points.irange(maximum=frame, inclusive=(True, False))
        # A SortedDict is just a b-list with a dict attached
        # so this is really the most efficient way to get an irange with values.
        # https://stackoverflow.com/questions/34099308/iterate-over-a-slice-of-items-in-a-sorteddict
        return ((k, self.points[k]) for k in keys)

    def add(self, frame, point):
        """
        Add a point at the frame
        :raise PointOverrideException: If a point already exists at the frame
        """
        v = self.points.setdefault(frame, point)  # won't add the point if the frame is already filled
        if v is not point:
            raise PointOverrideException("can't have the same track in two places at the same frame")

    def del_point_floor(self, frame):
        """
        Deletes the first point that occurs before the frame
        :returns: the deleted point, or None if no points were deleted
        """
        k = next(iter(self.points.irange(None, frame, reverse=True)), None)
        if not k:
            return None
        v = self.points.pop(k)
        return v

    def key_span(self):
        """
        Get the first and last frames of the track, or None if the track is empty
        """
        if not self.points:
            return None
        k = self.points.keys()
        return k[0], k[-1]

    def value_span(self):
        """
        Get the first and last points of the track, or None if the track is empty
        """
        if not self.points:
            return None
        v = self.points.values()
        return v[0], v[-1]

    def __str__(self):
        return f'Track({self.id})'

    def distance(self):
        """
        :return: the distance of the path, in pixels
        """
        ret = 0
        prev = None
        for x, y in self.points.values():
            if prev:
                ret += ((x - prev[0]) ** 2 + (y - prev[1]) ** 2) ** 0.5
            prev = (x, y)
        return ret

    def stats(self, **kwargs: Optional[str]):
        """
        Get genric stats about the track
        :param kwargs: additional tracks to add to the stats. If the value is falsish, the argument is skipped.
                        If it's True, the key name is appended.
                        Otherwise, the key and the value names are appended
        """
        ret = [str(self), ': ', str(len(self.points)), ' points']
        if self.points:
            ret.extend([', frame range: ', str(self.key_span()), ', value range: ', str(self.value_span()), ])
        if self.tags:
            ret.extend([', tags: ', '[', ', '.join(self.tags), ']'])
        ret.extend([', distance: ', str(int(self.distance())), 'px'])
        for k, v in kwargs.items():
            if not v:
                continue
            if v is True:
                ret.extend([', ', k])
            else:
                ret.extend([', ', k, ': ', str(v)])
        return ''.join(ret)
