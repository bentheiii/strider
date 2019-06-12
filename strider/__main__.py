# todo split this file it is gigantic
import argparse
import textwrap
import importlib.util
import warnings
import sys
import json
import itertools as it
import os.path as path

from sys import exit

import cv2
import strider
from strider import TrackPack
from strider.rectangle import Rectangle
from strider.__util__ import *

if strider.__dev__:
    print('you are using a development version of strider, install and use a release version unless'
          ' you know what you are doing', file=sys.stderr)

parser = argparse.ArgumentParser('strider', fromfile_prefix_chars='@',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('trackpack_path', action='store', default='?', nargs='?',
                    help='path to the trackpack file, default is to prompt')
parser.add_argument('video_path', action='store', default='?', nargs='?',
                    help='path to the source video, default is to load from trackpack file, or prompt')
parser.add_argument('--frame_step', action='store', type=int, help='set the regular play speed in frames',
                    default=1, required=False, dest='step')
parser.add_argument('--seek_step', action='store', type=float,
                    help='set the regular step in seconds',
                    default=1, required=False, dest='seek_step')
parser.add_argument('--move_step', action='store', type=int,
                    help='the size, in pixels, of movement of the zoomed view',
                    default=10, required=False, dest='move_step')
parser.add_argument('--zoom_step', action='store', type=float, help='the zoom step',
                    default=2, required=False, dest='zoom_step')
parser.add_argument('--point_radius', action='store', type=int, help='the radius of points',
                    default=5, required=False, dest='point_radius')
parser.add_argument('--line_width', action='store', type=int, help='the width of lines',
                    default=2, required=False, dest='line_width')
parser.add_argument('--auto_play_wait', action='store', type=int,
                    help='the time to wait between auto-play frames',
                    default=5, required=False, dest='auto_play_wait')

# raise is always true in dev mode
parser.add_argument('--raise', action='store_true', default=strider.__dev__, required=False, dest='raise_',
                    help='raise and quit on exceptions that would normally be caught, use when debugging')

# all options below here exit the program if used
parser.add_argument('--calibrate', action=strider.CalibrateAction, nargs='?', choices=['all'],
                    help='run the calibration process and exit,'
                         ' entering --calibrate all will also calibrate the common ascii keys')
parser.add_argument('--version', action='version', version=strider.__version__)


def maybe_import(module_name, var_name, var_type=object, default=None, report=True, **kwargs):
    try:
        spec = importlib.util.spec_from_file_location('', '__calibration__.py')
        if not spec:
            return default
    except ImportError:
        return default

    mod = importlib.util.module_from_spec(spec)
    for k, v in kwargs.items():
        setattr(mod, k, v)
    spec.loader.exec_module(mod)

    try:
        v = getattr(mod, var_name)
    except AttributeError:
        warnings.warn(f'module {module_name} has been imported, but variable {var_name} does not exist.')
        return default

    if not isinstance(v, var_type):
        warnings.warn(
            f'module {module_name} has been imported, but variable {var_name} is not of the proper type ({var_type}).')
        return default

    if report:
        print(f'using {var_name} from {module_name}')
    return v


tk = None
tk_filedialog = None
tk_messagebox = None


def init_tk():
    global tk, tk_filedialog, tk_messagebox
    if not tk:
        try:
            import tkinter as tk
            import tkinter.filedialog as tk_filedialog
            import tkinter.messagebox as tk_messagebox
        except ImportError as e:
            raise ImportError('cannot import tkinter, source path must be set in arguments') from e

        root = tk.Tk()
        root.withdraw()


def main(args=None):
    if args is None or isinstance(args, list):
        args = parser.parse_args(args)

    # this global variable is required because the trackbar causing a redraw even when the trackbar moved because of
    # the redraw
    # (since programmatically moving the trackbar also triggers its callback, in true cv2 fashion)
    suppress_trackbar_seek = BoolBox()

    # to disable clicks while we don't want them (e.g. when entering special commands)
    suppress_click = BoolBox()

    # to tell if we should even wait for keystroke
    auto_play = False

    codes = maybe_import('__calibration__', '__codes__', strider.Codes, Codes=strider.Codes) or strider.Codes()

    strider.KeyCommand.import_codes(codes)

    def on_mouse(event, x, y, flags, param):
        if suppress_click:
            return
        real = view.view_window.local_to_real(x, y)
        if event == cv2.EVENT_LBUTTONDOWN:
            print(f'({x}, {y}) (Real: {real})')
            if view.active_track:
                try:
                    view.add_point((x, y))
                except strider.PointOverrideException as e:
                    print('point not added: ' + str(e))
                else:
                    this_frame()
            else:
                print('no active track, use activate or new_track to activate a track')
        elif event == cv2.EVENT_RBUTTONDOWN:
            detected = list(view.detect_points((x, y)))
            if detected:
                print(f'({x}, {y}) (Real: {real}):')
                for t, f, (p_x, p_y) in detected:
                    print(f'\t({p_x}, {p_y}) at frame {f}, {t}')
            else:
                print(f'({x}, {y}) (Real: {real}): no points detected')

    def on_trackbar(pos, userdata=...):
        if suppress_trackbar_seek:
            return
        frame_ind = pos * view.fps
        view.seek(frame_ind)
        next_frame()

    def show_frame(frame):
        with suppress_trackbar_seek:
            cv2.setTrackbarPos('position', 'strider', int(view.next_frame_index // view.fps))
        cv2.imshow('strider', frame)

    def next_frame():
        frame = view.get_next_frame()
        if frame is None:
            return None
        frame = view.render_frame(frame)
        show_frame(frame)
        return frame

    def this_frame():
        frame = view.render_frame(view.get_this_frame())
        show_frame(frame)

    def info_msg():
        d = (
            ('source video', video_path),
            ('source tracks', pack_path),
            ('next frame', view.next_frame_index),
            ('total frames', view.total_frames),
            ('current time (approx)', ts_to_str(*view.curr_time_approx())),
            ('total time (approx)', ts_to_str(*view.total_time_approx())),
            ('active track', view.active_track),
            ('video dimensions', view.real_view.size),
            ('video fps', view.fps),
            ('view rectangle', repr(view.view_window)),
            ('zoom', 'x' + str(view.real_view.size_ratio(view.view_window))),
            ('quick tags', str(quick_tags)),
        )
        return 'INFO:\n' + '\n'.join(f'\t{n}: {v}' for n, v in d)

    def help_msg():
        additional_help = [
            "left click: add a point, at the current frame, to the active track",
            "right click: list the point(s) at the clicked area",
            ""
        ]
        return '\n'.join(it.chain(
            additional_help,
            (kc.__doc__ for kc in strider.KeyCommand.values())
        ))

    def report_jump(frame):
        print(f'jumped to frame {frame}, approx {ts_to_str(*view.approx_frame_to_time(frame, True))}')

    @strider.SpecialCommand
    def toggle_track(tid):
        """Toggle whether track is enabled"""
        view.track_pack.toggle_track(tid)
        this_frame()
        f'track {tid} toggled'

    @strider.SpecialCommand
    def activate(tid):
        """Activate a track"""
        t = view.activate_track(tid)
        print(f'track {t} active!')

    @strider.SpecialCommand
    def new_track(id_):
        """Create and activate a new track, with the specified ID"""
        t = view.new_track(id_=id_, activate=True)
        print(f'new track {t} active')

    @strider.SpecialCommand
    def seek(frame_ind):
        """Jump to a specific frame"""
        if isinstance(frame_ind, str):
            frame_ind = int(frame_ind)
        view.seek(frame_ind)
        report_jump(frame_ind)
        next_frame()

    @strider.SpecialCommand
    def seek_time(seconds, minutes=0, hours=0):
        """Jump to a specific time in seconds"""
        if isinstance(seconds, str):
            seconds = int(seconds)
        if isinstance(minutes, str):
            minutes = int(minutes)
        if isinstance(hours, str):
            minutes = int(hours)
        seconds += minutes * 60 + hours * 60 * 60

        frame_ind = int(seconds * view.fps)
        return seek(frame_ind)

    @strider.SpecialCommand
    def delete_track(tid):
        """Delete a track"""
        t = view.delete_track(tid)
        print(f'track {t} deleted')
        this_frame()

    @strider.SpecialCommand
    def tag(tag, tid=None):
        """Give a track a specified tag"""
        if tid is None:
            if not view.active_track:
                print('no active track')
                return
            tid = ...
        tag = tag.lower()
        t = view.add_tag(tid, tag=tag)
        if tag not in quick_tags:
            quick_tags.add(tag)
        print(f'tag {tag} added to {t}')

    @strider.SpecialCommand
    def remove_tag(tag, tid=None):
        """Remove a specified tag from a track"""
        if tid is None:
            if not view.active_track:
                print('no active track')
                return
            tid = ...
        tag = tag.lower()
        t, tag = view.remove_tag(tid, tag=tag)
        if t:
            print(f'tag {tag} removed from {t}')
        else:
            print(f'track {t} doesn\'t have tag {tag}')
        if not track_pack.has_tag(tag):
            quick_tags.remove(tag)

    @strider.SpecialCommand
    def enable_tag(tag):
        """Enable all tracks with a tag"""
        tag = tag.lower()
        view.enable_all(tag)
        print(f'all tracks with tag {tag} enabled')

    @strider.SpecialCommand
    def disable_tag(tag):
        """Disable all tracks with a tag"""
        tag = tag.lower()
        view.disable_all(tag)
        print(f'all tracks with tag {tag} disabled (except for active track)')

    @strider.key_command(codes.space, doc_placeholders=(args.step,))
    def step_forward():
        """Step forward {!n:frame}"""
        if next_frame() is None:
            print('end of video')
        if force_flush:  # todo look more into why we need this (for 4k videos)
            # https://stackoverflow.com/questions/52038222/opencv-python-window-not-refreshing-4k-videos-unless-calling-waitkey1
            cv2.waitKey(1)

    @strider.key_command(codes.left, doc_placeholders=(args.seek_step,))
    def step_backwards():
        """Step backwards {!n:second}"""
        view.back_step()
        next_frame()

    @strider.key_command(codes.right, doc_placeholders=(args.seek_step,))
    def step_forwards():
        """Step forwards {!n:second}"""
        view.fore_step()
        next_frame()

    @strider.key_command(codes.z, allow_on_auto_play=True, doc_placeholders=(args.zoom_step,))
    def zoom_in():
        """Zoom in x{}"""
        view.zoom_in(args.zoom_step)
        this_frame()

    @strider.key_command(codes.shift_z, allow_on_auto_play=True, doc_placeholders=(args.zoom_step,))
    def zoom_out():
        """Zoom out x{}"""
        view.zoom_out(args.zoom_step)
        this_frame()

    @strider.key_command(codes.esc, allow_on_auto_play=True)
    def quit():
        """Exit the program"""
        return True

    @strider.key_command(codes.a, allow_on_auto_play=True, doc_placeholders=(args.move_step,))
    def move_left():
        """Move the view left {!n:pixel}"""
        view.move_view(x_off=-args.move_step)
        this_frame()

    @strider.key_command(codes.d, allow_on_auto_play=True, doc_placeholders=(args.move_step,))
    def move_right():
        """Move the view right {!n:pixel}"""
        view.move_view(x_off=args.move_step)
        this_frame()

    @strider.key_command(codes.w, allow_on_auto_play=True, doc_placeholders=(args.move_step,))
    def move_up():
        """Move the view up {!n:pixel}"""
        view.move_view(y_off=-args.move_step)
        this_frame()

    @strider.key_command(codes.s, allow_on_auto_play=True, doc_placeholders=(args.move_step,))
    def move_down():
        """Move the view down {!n:pixel}"""
        view.move_view(y_off=args.move_step)
        this_frame()

    @strider.key_command(codes.n)
    def create_new_track():
        """Create and activate a new track with a semi-random id"""
        new_track(...)

    @strider.key_command(codes.g)
    def assign_tag_input():
        """Assign a tag to the active tag, chosen from the quick tags"""
        if not view.active_track:
            print('no active track')
        else:
            with suppress_click:
                t = quick_tags.input('type tag (<tab>-autocomplete, <esc>-cancel)', codes, report=True)
            if t:
                tag(t)

    @strider.key_command(codes.shift_g)
    def remove_tag_input():
        """Assign a tag to the active tag, chosen from the quick tags"""
        if not view.active_track:
            print('no active track')
        else:
            with suppress_click:
                t = quick_tags.input('type tag (<tab>-autocomplete, <esc>-cancel)', codes, report=True)
            if t:
                remove_tag(t)

    @strider.key_command(codes.h)
    def help():
        """Display this help message"""
        print('HELP:\n', textwrap.indent(help_msg(), prefix='\t'))

    @strider.key_command(codes.i)
    def info():
        """Show general variable information about the strider environment"""
        print(info_msg())

    @strider.key_command(codes.t)
    def list_tracks():
        """List all the tracks, and some information about them"""
        ret = [f'TRACKS ({len(view.track_pack.tracks)} total):']
        for t in view.tracks_sorted():
            if isinstance(t, str):
                ret.append(t + ':')
                continue
            stats = t.stats(enabled=str(view.track_pack.is_enabled(t)), active=view.active_track is t)
            ret.append(f'\t{stats}')
        print('\n'.join(ret))

    @strider.key_command(codes.r)
    def jump_to_zero():
        """Jump to the first frame of the video"""
        view.reset()
        report_jump(0)
        next_frame()

    @strider.key_command(codes.home)
    def jump_to_start():
        """Jump to the start of the current track"""
        if not view.active_track:
            print('no active track')
        else:
            span = view.active_track.key_span()
            if not span:
                print('active track is empty')
            else:
                view.seek(span[0])
                report_jump(span[0])
                next_frame()

    @strider.key_command(codes.end)
    def jump_to_end():
        """Jump to the end of the active track"""
        if not view.active_track:
            print('no active track')
        else:
            span = view.active_track.key_span()
            if not span:
                print('active track is empty')
            else:
                view.seek(span[1])
                report_jump(span[1])
                next_frame()

    @strider.key_command(codes.p)
    def save_tracks():
        """Save the tracks to the designated json file"""
        with open(pack_path, 'w') as w:
            view.track_pack.write(w)
        print('saved!')

    @strider.key_command(codes.u)
    def undo():
        """Remove last point (up to current frame) in the active track"""
        if not view.active_track:
            print('no active track')
        else:
            deleted = view.del_last_point()
            this_frame()
            print(f'point deleted: {deleted}')

    @strider.key_command(codes.q)
    def batch_enable():
        """Enable tracks by a specified quick tag (or space to enable all)"""
        with suppress_click:
            t = quick_tags.input('type tag (<tab>-autocomplete, <esc>-cancel, blank for all)', codes, report=True)
        if t is '':
            view.enable_all()
            print('all tracks enabled')
        elif t is None:
            print('cancelled')
        else:
            enable_tag(t)
        this_frame()

    @strider.key_command(codes.shift_q)
    def batch_disable():
        """Disable tracks by quick tag (or space to enable all), except the active track, if it exists"""
        with suppress_click:
            t = quick_tags.input('type tag (<tab>-autocomplete, <esc>-cancel, blank for all)', codes, report=True)
        if t is '':
            view.disable_all()
            print('all tracks disabled (except for active track)')
        elif t is None:
            print('cancelled')
        else:
            disable_tag(t)
        this_frame()

    @strider.key_command(codes.tab)
    def start_auto_play():
        """Enable auto-play, will continue the video until a key is pressed.
         Some keys (zoom, move zoomed rectangle, ...) will not stop the auto-play."""
        nonlocal auto_play
        auto_play = True
        print("started auto-play, press tab again to end")

    @strider.key_command(codes.c)
    def special_command():
        """Run a special command as typed:"""
        with suppress_click:
            line_edit = strider.LineEdit(report=True, autocomplete=strider.SpecialCommand.keys())
            line = line_edit.cv_input('enter command (tab to autocomplete, esc to cancel)', codes)

        if line:
            try:
                comm, arguments = strider.SpecialCommand.parse_func_call(line)
            except (KeyError, ValueError) as e:
                print('could not parse line, reason: ' + str(e))
            else:
                try:
                    comm(*arguments)
                except Exception as e:
                    if args.raise_:
                        raise
                    print(f'failed: {type(e)}: {e}')

    special_command.__doc__ += ''.join('\n\t' + sc.__doc__ for sc in strider.SpecialCommand.values())

    pack_path = args.trackpack_path
    if pack_path == '?':
        init_tk()
        pack_path = tk_filedialog.asksaveasfilename(
            defaultextension='json', filetypes=['json {.json .stp}', '{all files} *'],
            title='choose a trackpack file to use', confirmoverwrite=False
        )
        if not pack_path:
            print('cancelled')
            exit()

    try:
        with open(pack_path) as r:
            track_pack = TrackPack.read(r)
    except (json.JSONDecodeError, KeyError) as e:
        raise Exception('could not open file') from e
    except FileNotFoundError:
        print(f'new file created: {pack_path}')
        track_pack = TrackPack(name=pack_path)

    quick_tags = strider.QuickTagRepo(track_pack.all_tags())

    video_path = args.video_path
    if video_path == '?':
        if track_pack.video_path and path.exists(track_pack.video_path):
            video_path = track_pack.video_path
        else:
            init_tk()
            video_path = tk_filedialog.askopenfilename(
                filetypes=['video {.mp4 .mov .avi .mkv}', '{all files} *'], title='choose a video file to open'
            )
            if not video_path:
                print('cancelled')
                exit()

    if track_pack.video_path != video_path:
        try:
            init_tk()
        except ImportError:
            pass
        else:
            if tk_messagebox.askyesno(
                    'set default source',
                    "the selected video is different from the trackpack's default,"
                    " would you like to set it as default?"):
                track_pack.video_path = video_path

    view = strider.StriderView(track_pack=track_pack, video_source_path=video_path,
                               play_step_frame=args.step, seek_step_sec=args.seek_step,
                               line_width=args.line_width, point_radius=args.point_radius)
    view.track_pack.enable_all()

    force_flush = view.real_view.breaks_bounds(Rectangle(0, 0, 2000, 1100))

    cv2.namedWindow('strider', cv2.WINDOW_NORMAL)
    cv2.setMouseCallback('strider', on_mouse)
    cv2.createTrackbar('position', 'strider', 0, int(view.total_frames // view.fps), on_trackbar)
    next_frame()

    while True:
        if auto_play:
            key = cv2.waitKeyEx(args.auto_play_wait)
            comm = strider.KeyCommand.get(key)  # comm will be None if no key button was pressed
            end_auto_play = comm and not comm.allow_on_auto_play
            if end_auto_play:
                auto_play = False
                print('ended auto-play')
            else:
                if comm:
                    if comm():
                        break
                else:
                    next_frame()
        else:
            key = cv2.waitKeyEx()
            comm = strider.KeyCommand.get(key)
            if not comm:
                print('unhandled key code ' + str(key) + (f' (chr: {chr(key)!r} )' if 0 <= key <= 0x10ffff else '')
                      + ' if this is supposed to be a valid key, run the calibration command (strider --calibrate) '
                        'to run calibration')
            elif comm():
                break


cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
