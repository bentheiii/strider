from typing import Set

from strider.line_edit import LineEdit


class QuickTagRepo(Set[str]):
    def input(self, prompt, codes, **kwargs):
        edit = LineEdit(autocomplete=self, **kwargs)
        return edit.cv_input(prompt, codes)

    def __str__(self):
        return f'({len(self)}): {sorted(self)}'
