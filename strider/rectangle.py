from typing import Tuple


class Rectangle:
    def __init__(self, offsetx, offsety, width, height):
        self.offset_x = int(offsetx)
        self.offset_y = int(offsety)
        self.size_x = int(width)
        self.size_y = int(height)

    def local_to_real(self, x, y):
        return x + self.offset_x, y + self.offset_y

    def real_to_local(self, x, y) -> Tuple[bool, Tuple[int, int]]:
        """
        :return: a 2-tuple: whether the real point is inside the rectangle, and the local point
        """
        return (self.offset_x <= x < self.offset_x + self.size_x
                and self.offset_y <= y < self.offset_y + self.size_y), (x - self.offset_x, y - self.offset_y)

    def slice_frame(self, frame):
        """
        This also returns a copy of the frame so we can edit it without polluting the cache
        """
        return frame[
               self.offset_y: self.offset_y + self.size_y,
               self.offset_x: self.offset_x + self.size_x,
               ].copy()

    def breaks_bounds(self, master: 'Rectangle'):
        return self.offset_x < master.offset_x \
               or self.offset_y < master.offset_y \
               or self.offset_x + self.size_x > master.offset_x + master.size_x \
               or self.offset_y + self.size_y > master.offset_y + master.size_y

    def move(self, x_off, y_off, master: 'Rectangle' = None)->'Rectangle':
        ret = type(self)(self.offset_x + x_off, self.offset_y + y_off, self.size_x, self.size_y)
        if master and ret.breaks_bounds(master):
            return self
        return ret

    def zoom_to_center(self, other: float):
        """
        Returns a new rectangle, one nth the size on each side and centered on the original rectangle
        """
        offset_coff = (other - 1) / (2 * other)
        ret = type(self)(self.offset_x + self.size_x * offset_coff, self.offset_y + self.size_y * offset_coff,
                         self.size_x // other, self.size_y // other)
        if min(ret.size) < 1:  # prevent a rectangle with 0 size
            return self
        return ret

    def size_ratio(self, other: 'Rectangle'):
        """
        calculate the ratio of sizes between self and other.
        already assumes the two rectangles have the same ratio, and only uses x
        R / (R // x) == x
        """
        return self.size_x / other.size_x

    def zoom_from_center(self, other, master: 'Rectangle' = None)-> 'Rectangle':
        """
        note, if the new rectangle is outside master *in any way*, it returns master instead
        the only guarantee is that if R < M:
        (R // n).undiv(n, M) == R
        """
        offset_coff = (other - 1) / 2
        ret = type(self)(self.offset_x - self.size_x * offset_coff, self.offset_y - self.size_y * offset_coff,
                         self.size_x * other, self.size_y * other)
        if master and ret.breaks_bounds(master):
            return master
        return ret

    @property
    def size(self):
        return self.size_x, self.size_y

    def __repr__(self):
        return f'Rectangle({self.offset_x}, {self.offset_y}, {self.size_x}, {self.size_y})'
