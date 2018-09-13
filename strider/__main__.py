import argparse
import textwrap
import importlib
import warnings
import sys
import itertools as it
from collections import ChainMap
from collections.abc import Mapping

import cv2
import strider
from strider.__util__ import *

if strider.__dev__:
    print('you are using a development version of strider, install and use a release version unless'
          ' you know what you are doing', file=sys.stderr)


class Calibrate(argparse.Action):
    # calibrate action
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('default', argparse.SUPPRESS)
        super().__init__(*args, **kwargs)

    def __call__(self, parser_, namespace, values, option_string=None):
        ret = ['__codes__ = {']
        cv2.imshow('calibration', 0)

        if values == 'all':
            print('enter backspace')
            backspace_code = cv2.waitKeyEx()
            if backspace_code != Codes.backspace:
                ret.append(f'\t"backspace": {backspace_code},')
            print('enter esc')
            esc_code = cv2.waitKeyEx()
            if esc_code != Codes.esc:
                ret.append(f'\t"esc": {esc_code}')
        else:
            backspace_code = Codes.backspace
            esc_code = Codes.esc

        for name, v in Codes.__dict__.items():
            if name.startswith('_'):
                continue
            if (not values == 'all') and v < 128:
                continue

            print(f'enter code for {name}, backspace to not register this key, or esc to quit and save calibration')
            code = cv2.waitKeyEx()
            if code == backspace_code:
                continue
            elif code == esc_code:
                break
            if code == v:
                print(f'"{name}": {code!r}, same as default')
            else:
                ret.append(f'\t"{name}": {code!r},')
                print(f'"{name}": {code!r}')
        ret.append('}')
        with open('__calibration__.py', 'w') as w:
            w.write('\n'.join(ret))
        print('calibration saved to __calibration__.py')
        exit()


class DeprecatedAction(argparse.Action):
    """
    Informs the user the option has been deprecated
    """

    def __init__(self, *args, use_instead: str, **kwargs):
        kwargs.setdefault('help', argparse.SUPPRESS)
        super().__init__(*args, **kwargs)
        self.use_instead = use_instead

    def __call__(self, parser_, namespace, values, option_string=None):
        warnings.warn(DeprecationWarning(
            f'{option_string} is deprecated, use {self.use_instead} instead, argument ignored'))


parser = argparse.ArgumentParser('strider', fromfile_prefix_chars='@',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('src_path', action='store', help='path to the source video')
parser.add_argument('tracks_path', action='store', help='path to the trackpack file')
parser.add_argument('-t', '--tags', action='store', nargs='+', type=str, help='path to a quick tags file',
                    required=False, default=[], dest='quick_tags_path')
parser.add_argument('-qt', action='store', nargs='+', type=str, help='quick tags to add', required=False,
                    default=[], dest='quick_tags')
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
parser.add_argument('--force_flush', action='store_true', dest='force_flush', required=False,
                    default=False, help='set to force flushing on every frame (useful for 4k videos)')

# raise is always true in dev mode
parser.add_argument('--raise', action='store_true', default=strider.__dev__, required=False, dest='raise_',
                    help='raise and quit on exceptions that would normally be caught, use when debugging')

# all options below here exit the program if used
parser.add_argument('--calibrate', action=Calibrate, nargs='?', choices=['all'],
                    help='run the calibration process and exit,'
                         ' entering --calibrate all will also calibrate the common ascii keys')
parser.add_argument('--version', action='version', version=strider.__version__)

# deprecated (do not end the program)
parser.add_argument('--step', action=DeprecatedAction, use_instead='--frame_step')
parser.add_argument('--back_step', '--backstep', action=DeprecatedAction, use_instead='--seek_step')
parser.add_argument('--linewidth', action=DeprecatedAction, use_instead='--line_width')
parser.add_argument('--pointradius', action=DeprecatedAction, use_instead='--point_radius')


class Codes:
    # a static class containing all the key codes the program needs. These values can be overridden
    # by the calibration file
    right = 2555904
    left = 2424832
    home = 2359296
    end = 2293760

    # everything below here is ascii
    esc = 27
    backspace = 8
    space = ord(' ')
    enter = ord('\r')
    tab = ord('\t')

    a = ord('a')
    c = ord('c')
    d = ord('d')
    g = ord('g')
    h = ord('h')
    i = ord('i')
    n = ord('n')
    p = ord('p')
    q = ord('q')
    r = ord('r')
    s = ord('s')
    t = ord('t')
    u = ord('u')
    w = ord('w')
    z = ord('z')

    shift_q = ord('Q')
    shift_z = ord('Z')


def maybe_import(module_name, var_name, var_type=object, default=None, report=True):
    try:
        mod = importlib.import_module(module_name)
    except ImportError:
        return default

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


def main(args=None):
    args = parser.parse_args(args)

    # this global variable is required because the trackbar causing a redraw even when the trackbar moved because of
    # the redraw
    # (since programmatically moving the trackbar also triggers its callback, in true cv2 fashion)
    suppress_trackbar_seek = False

    # to disable clicks while we don't want them (e.g. when entering special commands)
    suppress_click = False

    # to tell if we should even wait for keystroke
    auto_play = False

    user_codes = maybe_import('__calibration__', '__codes__', dict, {})
    for name, v in user_codes.items():
        if not hasattr(Codes, name):
            raise AttributeError(name)
        setattr(Codes, name, v)

    strider.KeyCommand.code_dict = Codes.__dict__

    quick_tags = set(x.lower() for x in args.quick_tags)
    if args.quick_tags_path:
        for qtp in args.quick_tags_path:
            with open(qtp) as r:
                r = (x.lower().strip() for x in r)
                quick_tags.update(r)
    if quick_tags:
        quick_tags, num = strider.resolve_quick_tags(sorted(quick_tags))
        print(f'loaded {num} quick tags')
        if not num:
            quick_tags = None
    else:
        quick_tags = None

    def get_cv_input(prompt):
        nonlocal suppress_click
        suppress_click = True
        print(prompt)
        edit = strider.LineEdit(report=True)
        while True:
            code = cv2.waitKeyEx()
            if code == Codes.backspace:
                edit.backspace()
            elif code == Codes.enter:
                ret = edit.enter()
                break
            elif code == Codes.esc:
                print('..cancelled')
                ret = None
                break
            elif code == Codes.right:
                edit.right()
            elif code == Codes.left:
                edit.left()
            elif code == Codes.home:
                edit.home()
            elif code == Codes.end:
                edit.end()
            elif code < 128:
                c = chr(code) if code < 0x110000 else ''
                edit.feed(c)
        suppress_click = False
        return ret

    no_default = object()  # singleton to fail on no tags

    def get_quick_tag(additional_codes={}, default=no_default):
        if not quick_tags:
            if default is no_default:
                raise Exception('no quick tags are configured')
            return default
        print('QUICK TAGS:')
        tag_dict = ChainMap(quick_tags, additional_codes)
        while isinstance(tag_dict, Mapping):
            for k, m, _ in tag_dict.values():
                print(f'\t{k}: {m}')
            code = cv2.waitKeyEx()
            if code in tag_dict:
                _, _, tag_dict = tag_dict[code]
            else:
                print('code not recognized')
        return tag_dict

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
        nonlocal suppress_trackbar_seek
        suppress_trackbar_seek = True
        cv2.setTrackbarPos('position', 'strider', int(view.next_frame_index // view.fps))
        suppress_trackbar_seek = False
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
            ('source video', args.src_path),
            ('source tracks', args.tracks_path),
            ('next frame', view.next_frame_index),
            ('total frames', view.total_frames),
            ('current time (approx)', ts_to_str(*view.curr_time_approx())),
            ('total time (approx)', ts_to_str(*view.total_time_approx())),
            ('active track', view.active_track),
            ('video dimensions', view.real_view.size),
            ('video fps', view.fps),
            ('view rectangle', repr(view.view_window)),
            ('zoom', 'x' + str(view.real_view.size_ratio(view.view_window))),
            ('quick tags', ', '.join(strider.tag_names(quick_tags))),
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
        print(f'jumped to frame {frame}, approx {ts_to_str(*view.approx_frame_to_time(frame,True))}')

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

    @strider.key_command(Codes.space)
    def step_forward():
        """Step forward one frame, or amount specified in the arguments"""
        if next_frame() is None:
            print('end of video')
        if args.force_flush:  # todo look more into why we need this (for 4k videos)
            # https://stackoverflow.com/questions/52038222/opencv-python-window-not-refreshing-4k-videos-unless-calling-waitkey1
            cv2.waitKey(1)

    @strider.key_command(Codes.left)
    def step_backwards():
        """Step backwards a second, or amount specified in the arguments"""
        view.back_step()
        next_frame()

    @strider.key_command(Codes.right)
    def step_forwards():
        """Step forwards a second, or amount specified in the arguments"""
        view.fore_step()
        next_frame()

    @strider.key_command(Codes.z, allow_on_auto_play=True)
    def zoom_in():
        """Zoom in x2, or amount specified in the arguments"""
        view.zoom_in(zoom_step)
        this_frame()

    @strider.key_command(Codes.shift_z, allow_on_auto_play=True)
    def zoom_out():
        """Zoom out x2, or amount specified in the arguments"""
        view.zoom_out(zoom_step)
        this_frame()

    @strider.key_command(Codes.esc, allow_on_auto_play=True)
    def quit():
        """Exit the program"""
        return True

    @strider.key_command(Codes.a, allow_on_auto_play=True)
    def move_left():
        """Move the view left 10 pixels, or amount specified in the arguments"""
        view.move_view(x_off=-args.move_step)
        this_frame()

    @strider.key_command(Codes.d, allow_on_auto_play=True)
    def move_right():
        """Move the view right 10 pixels, or amount specified in the arguments"""
        view.move_view(x_off=args.move_step)
        this_frame()

    @strider.key_command(Codes.w, allow_on_auto_play=True)
    def move_up():
        """Move the view up 10 pixels, or amount specified in the arguments"""
        view.move_view(y_off=-args.move_step)
        this_frame()

    @strider.key_command(Codes.s, allow_on_auto_play=True)
    def move_down():
        """Move the view down 10 pixels, or amount specified in the arguments"""
        view.move_view(y_off=args.move_step)
        this_frame()

    @strider.key_command(Codes.n)
    def create_new_track():
        """Create and activate a new track with a semi-random id"""
        new_track(...)

    @strider.key_command(Codes.g)
    def assign_quick_tag():
        """Assign a tag to the active tag, chosen from the quick tags"""
        if not quick_tags:
            print('no quick tags, use -t ro configure quick tags')
        elif not view.active_track:
            print('no active track')
        else:
            t = get_quick_tag()
            if t:
                tag(t)
            else:
                print('cancelled')

    @strider.key_command(Codes.h)
    def help():
        """Display this help message"""
        print('HELP:\n', textwrap.indent(help_msg(), prefix='\t'))

    @strider.key_command(Codes.i)
    def info():
        """Show general variable information about the strider environment"""
        print(info_msg())

    @strider.key_command(Codes.t)
    def list_tracks():
        """List all the tracks, and some information about them"""
        ret = [f'TRACKS ({len(view.track_pack.tracks)} total):']
        for t in view.tracks_sorted():
            stats = t.stats(enabled=str(view.track_pack.is_enabled(t)), active=view.active_track is t)
            ret.append(f'\t{stats}')
        print('\n'.join(ret))

    @strider.key_command(Codes.r)
    def jump_to_zero():
        """Jump to the first frame of the video"""
        view.reset()
        report_jump(0)
        next_frame()

    @strider.key_command(Codes.home)
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

    @strider.key_command(Codes.end)
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

    @strider.key_command(Codes.p)
    def save_tracks():
        """Save the tracks to the designated json file"""
        with open(args.tracks_path, 'w') as w:
            view.track_pack.write(w)
        print('saved!')

    @strider.key_command(Codes.u)
    def undo():
        """Remove last point (up to current frame) in the active track"""
        if not view.active_track:
            print('no active track')
        else:
            deleted = view.del_last_point()
            this_frame()
            print(f'point deleted: {deleted}')

    @strider.key_command(Codes.q)
    def batch_enable():
        """Enable tracks by a specified quick tag (or space to enable all)"""
        t = get_quick_tag({Codes.space: ('space', '<all>', ...)}, default=...)
        if t is ...:
            view.enable_all()
            print('all tracks enabled')
        elif t is None:
            print('cancelled')
        else:
            enable_tag(t)
        this_frame()

    @strider.key_command(Codes.shift_q)
    def batch_disable():
        """Disable tracks by quick tag (or space to enable all), except the active track, if it exists"""
        t = get_quick_tag({Codes.space: ('space', '<all>', ...)}, default=...)
        if t is ...:
            view.disable_all()
            print('all tracks disabled (except for active track)')
        elif t is None:
            print('cancelled')
        else:
            disable_tag(t)
        this_frame()

    @strider.key_command(Codes.tab)
    def start_auto_play():
        """Enable auto-play, will continue the video until a key is pressed.
         Some keys (zoom, move zoomed rectangle, ...) will not stop the auto-play."""
        nonlocal auto_play
        auto_play = True
        print("started auto-play, press tab again to end")

    @strider.key_command(Codes.c)
    def special_command():
        """Run a special command as typed:"""
        line = get_cv_input('enter command:')
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

    zoom_step = args.zoom_step

    view = strider.StriderView(pack_path=args.tracks_path, video_source_path=args.src_path,
                               play_step_frame=args.step, seek_step_sec=args.seek_step,
                               line_width=args.line_width, point_radius=args.point_radius)
    view.track_pack.enable_all()

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
