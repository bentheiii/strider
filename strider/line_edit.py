from typing import List, Iterable

import cv2

class LineEdit:
    """
    This class implements a minimalistic text editor inside the standard output using parsed opencv codes
    """

    # NOTE: for now, this is untested on Linux
    def __init__(self, report=False, autocomplete: Iterable[str] = ()):
        self.autocomplete_candidates = autocomplete
        self.cursor = chr(9608)
        self.buffer: List[str] = []
        self.next_ind = 0
        self.report = report
        self.prev_printed = 0  # the length of the previously printed message (so we can clear it)
        self._report()

    def _print_clear(self, *args):
        """
        prints the message, adding enough whitespaces to cover the previous message
        """
        s = ''.join(str(i) for i in args)
        n = len(s)
        print(s, ' ' * (self.prev_printed - n), end='', flush=True, sep='')
        self.prev_printed = n

    def _report(self, cursor=True):
        """
        print the buffer state, clearing the previously printed line
        """
        if not self.report:
            return
        if not cursor:
            self._print_clear('\x0d', self.getvalue(), )
        else:
            self._print_clear('\x0d', ''.join(self.buffer[:self.next_ind]), self.cursor,
                              ''.join(self.buffer[self.next_ind:]), )

    def feed(self, chars: str):
        """
        Insert new characters at the cursor's location, overriding any existing characters in front of it
        """
        self.buffer[self.next_ind: self.next_ind] = list(chars)
        self.next_ind += len(chars)
        self.normalize_ind()
        self._report()

    def normalize_ind(self):
        """
        :return: whether the cursor hit a boundary
        """
        if self.next_ind < 0:
            self.next_ind = 0
            return True
        if self.next_ind > len(self.buffer):
            self.next_ind = len(self.buffer)
            return True
        return False

    def getvalue(self):
        return ''.join(self.buffer)

    def backspace(self):
        if self.next_ind == 0:
            return
        del self.buffer[self.next_ind - 1]
        self.next_ind -= 1
        self.normalize_ind()
        self._report()

    def left(self):
        self.next_ind -= 1
        if not self.normalize_ind():
            self._report()

    def right(self):
        self.next_ind += 1
        if not self.normalize_ind():
            self._report()

    def enter(self):
        self._report(cursor=False)
        if self.report:
            print()
        return self.getvalue()

    def home(self):
        self.next_ind = 0
        self._report()

    def end(self):
        self.next_ind = len(self.buffer)
        self._report()

    def autocomplete(self):
        value = self.getvalue()
        candidate = None
        for autocomplete_candidate in self.autocomplete_candidates:
            if autocomplete_candidate.startswith(value):
                if candidate:
                    return None
                else:
                    candidate = autocomplete_candidate
        if candidate:
            self.feed(candidate[len(value):])

    def cv_input(self, prompt, codes, on_cancel = None):
        print(prompt)
        while True:
            code = cv2.waitKeyEx()
            if code == codes.backspace:
                self.backspace()
            elif code == codes.enter:
                ret = self.enter()
                break
            elif code == codes.esc:
                if self.report:
                    print('..cancelled')
                ret = on_cancel
                break
            elif code == codes.right:
                self.right()
            elif code == codes.left:
                self.left()
            elif code == codes.home:
                self.home()
            elif code == codes.end:
                self.end()
            elif code == codes.tab:
                self.autocomplete()
            elif code < 128:
                c = chr(code)
                self.feed(c)
        return ret
