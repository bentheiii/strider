from strider.__data__ import *
from strider.strider_view import StriderView
from strider.commands import SpecialCommand, KeyCommand, key_command
from strider.track import PointOverrideException, Track
from strider.track_pack import TrackPack
from strider.quick_tags import QuickTagRepo
from strider.line_edit import LineEdit
from strider.cv_codes import Codes, CalibrateAction

__dev__ = "dev" in __version__

# todo freeze
# todo change all prints to log?

# todo autosave?

# todo bug: sometimes an extra point appears randomly after the track is saved
#  (i suspect the user simply pressed the windows by accident, but worth checking anyway)
