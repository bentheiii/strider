from strider.__data__ import *
from strider.strider_view import StriderView
from strider.commands import SpecialCommand, KeyCommand, key_command
from strider.track import PointOverrideException
from strider.quick_tags import resolve_quick_tags, tag_names
from strider.line_edit import LineEdit

__dev__ = "dev" in __version__

# todo quick-tags in command line
# todo make tag order deterministic
# todo does q, shift+q work without tags?
# todo click in "h"
# todo auto-walk
# todo step-forward
# todo license, readme
# todo add changelog
# todo bug
