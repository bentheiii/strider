import random
import os.path

import cv2

from strider.rectangle import Rectangle
from strider.track_pack import TrackPack
from strider.track import Track


class StriderView:
    """
    Manager for the strider MODEL.
    A bit of a borg class but it just co-ordinates between the video and the tracks so no real worries
    """

    def __init__(self, *, pack_path=None, video_source_path, active_track=None, view_window=..., play_step_frame=1,
                 seek_step_sec=1, line_width=2, point_radius=5, detection_radius: int = ...):
        self.play_step_frame = play_step_frame
        self.seek_step_seconds = seek_step_sec
        self.video_source = cv2.VideoCapture(video_source_path)
        self.line_width = line_width
        self.point_radius = point_radius
        if detection_radius is ...:
            # ~sqrt(2) to make the detection diamond cover all the circle's area
            detection_radius = self.point_radius * 1.14142
        self.detection_radius = detection_radius

        if not self.video_source.isOpened():
            raise Exception("Error opening video stream")

        if pack_path and os.path.isfile(pack_path):
            with open(pack_path) as r:
                self.track_pack = TrackPack.read(r)
        else:
            self.track_pack = TrackPack()

        self.next_frame_index = 0
        w = self.video_source.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = self.video_source.get(cv2.CAP_PROP_FRAME_HEIGHT)
        self.real_view = Rectangle(0, 0, w, h)
        self.fps = self.video_source.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.video_source.get(cv2.CAP_PROP_FRAME_COUNT))

        if view_window is ...:
            view_window = self.real_view

        self.view_window = view_window

        self.active_track: Track = None
        self.activate_track(active_track)

        self.this_frame = None

    def new_track(self, id_=..., enable=True, activate=False):
        if id_ is ...:
            id_ = self.track_pack.new_id()
        track = Track()
        track.id = id_
        # edit the json file if you want a specific color
        track.color = tuple(random.randint(0, 255) for _ in range(3))
        self.track_pack.add_track(track)
        if enable:
            self.track_pack.enable_track(track)
        if activate:
            self.active_track = track
        return track

    def activate_track(self, t):
        if t is None:
            self.active_track = None
            return None
        # we loosely expect the rule that the active track is enabled, so we enforce it here
        if isinstance(t, str):
            t = self.track_pack[t]
        self.active_track = t
        self.track_pack.enable_track(t)
        return t

    def get_next_frame(self):
        if not self.video_source.isOpened():
            raise Exception("Error opening video stream or file")
        for _ in range(self.play_step_frame):
            success = self.video_source.grab()
            if not success:
                return None
        _, frame = self.video_source.retrieve()
        self.next_frame_index += self.play_step_frame
        self.this_frame = frame
        return frame

    def get_this_frame(self):
        return self.this_frame

    def render_frame(self, frame):
        window_frame = self.view_window.slice_frame(frame)
        points = self.track_pack.under(self.next_frame_index)
        for t, point_list in points:
            color = t.color
            prev = None  # prev is in local coordinates
            prev_in = None
            for f, (x, y) in point_list:
                in_local, local = self.view_window.real_to_local(x, y)
                if in_local:
                    cv2.circle(window_frame, local, self.point_radius, color, thickness=-1)
                    if prev:
                        cv2.line(window_frame, prev, local, color, self.line_width)
                elif prev_in:
                    # if current is outside, but prev is inside, we need to draw a line to it
                    cv2.line(window_frame, prev, local, color, self.line_width)
                prev = local
                prev_in = in_local
        return window_frame

    def add_point(self, local_point, frame=..., track=...):
        if track is ...:
            track = self.active_track
        elif isinstance(track, str):
            track = self.track_pack[track]

        if frame is ...:
            frame = self.next_frame_index - self.play_step_frame
        point = self.view_window.local_to_real(*local_point)
        assert point is not None
        track.add(frame, point)

    def detect_points(self, local_point):
        r_x, r_y = self.view_window.local_to_real(*local_point)
        candidates = self.track_pack.under(self.next_frame_index)

        for t, point_list in candidates:
            for frame, (x, y) in point_list:
                # note, we check for manhattan distance instead of euclidean to save time (and code),
                # at these small ranges,they are pretty much the same, it just looks like a diamond
                # (we also enlarged the diamond's size to cover the entire circle)
                dist = abs(x - r_x) + abs(y - r_y)
                if dist < self.detection_radius:
                    yield (t, frame, (x, y))

    def move_view(self, x_off=0, y_off=0):
        self.view_window = self.view_window.move(x_off, y_off, master=self.real_view)

    def zoom_in(self, factor: int):
        view = self.view_window // factor
        self.view_window = view

    def zoom_out(self, factor: int):
        # note, if the view too near the real border, zoom_out will zoom out all the way to the real
        # (this is actually useful since if you're right near the border, you probably finished
        # a track and would like to zoom out all the way)
        view = self.view_window.undiv(factor, master=self.real_view)
        self.view_window = view

    def is_zoomed(self):
        return self.view_window is not self.real_view

    # note: seek, backstep, and reset all clear the frame cache, get_next_frame() must be called after
    # them before any work is to be done

    def back_step(self, amount=...):
        if amount is ...:
            amount = int(self.fps * self.seek_step_seconds)
        next_frame_index = max(self.next_frame_index - amount, 0)
        self.seek(next_frame_index)

    def fore_step(self, amount=...):
        if amount is ...:
            amount = int(self.fps * self.seek_step_seconds)
        next_frame_index = min(self.next_frame_index + amount, self.total_frames-1)
        self.seek(next_frame_index)

    def reset(self):
        self.seek(0)

    def seek(self, next_frame_ind):
        self.next_frame_index = next_frame_ind
        self.video_source.set(cv2.CAP_PROP_POS_FRAMES, next_frame_ind)
        self.this_frame = None

    def approx_frame_to_time(self, frame, round_=False):
        seconds = frame / self.fps
        if round_:
            seconds = round(seconds)
        hours = int(seconds // (60 * 60))
        seconds -= (hours * 60 * 60)
        minutes = int(seconds // 60)
        seconds -= (minutes * 60)
        sub_sec = seconds % 1
        seconds = int(seconds)
        return hours, minutes, seconds, sub_sec

    def curr_time_approx(self, round_=False):
        return self.approx_frame_to_time(self.next_frame_index - self.play_step_frame, round_=round_)

    def total_time_approx(self, round_=False):
        return self.approx_frame_to_time(self.total_frames, round_=round_)

    def del_last_point(self, track=...):
        """
        :return: the deleted point, or none if none deleted
        """
        if track is ...:
            track = self.active_track
        if isinstance(track, str):
            track = self.track_pack[track]
        try:
            return track.del_point_floor(self.next_frame_index - self.play_step_frame)
        except KeyError:
            return None

    def delete_track(self, track):
        track = Track.id(track)
        ret = self.track_pack.delete_track(track)
        if ret == self.active_track:
            self.activate_track(None)
        return ret

    def __del__(self):
        if self.video_source:
            self.video_source.release()

    def add_tag(self, track=..., *, tag: str):
        if track is ...:
            track = self.active_track
        if isinstance(track, str):
            track = self.track_pack[track]

        track.tags.add(tag)
        return track

    def enable_all(self, tag=None):
        if tag:
            for t in self.track_pack.disabled():
                if tag in t.tags:
                    self.track_pack.enable_track(t)
        else:
            self.track_pack.enable_all()

    def disable_all(self, tag=None):
        if tag:
            for t in self.track_pack.enabled():
                if tag in t.tags and (t is not self.active_track):
                    self.track_pack.disable_all()
        else:
            self.track_pack.disable_all()
            if self.active_track:
                self.track_pack.enable_track(self.active_track)
