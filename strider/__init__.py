from strider.__data__ import __version__, __author__
from strider.strider_view import StriderView
from strider.commands import SpecialCommand, KeyCommand, key_command
from strider.track import PointOverrideException
from strider.quick_tags import resolve_quick_tags, tag_names
from strider.line_edit import LineEdit
try:
    from strider.__dev__ import __dev__
except ImportError:
    pass

# todo auto-walk
# todo step-forward
# todo license, readme
# todo add changelog
# todo bug
