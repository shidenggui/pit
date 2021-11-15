from dataclasses import dataclass, field

from pit.constants import Color
from pit.diff import Line, Edit


@dataclass
class Hunk:
    a_start: int
    b_start: int
    edits: list[Edit] = field(default_factory=list)

    CONTEXT = 3

    def header(self):
        a_lines = len([edit for edit in self.edits if edit.a_line])
        b_lines = len([edit for edit in self.edits if edit.b_line])
        return f"{Color.CYAN}@@ -{self.a_start},{a_lines} +{self.b_start},{b_lines} @@{Color.RESET_ALL}"

    @classmethod
    def filters(cls, edits: list[Edit]):
        i = 0
        hunks = []
        while i < len(edits):
            while i < len(edits) and edits[i].type == " ":
                i += 1

            if i >= len(edits):
                break

            i -= cls.CONTEXT
            hunk = (
                Hunk(0, 0)
                if i < 0
                else Hunk(edits[i].a_line.number, edits[i].b_line.number)
            )

            i = max(i, 0)
            while edits[i].type == " ":
                hunk.edits.append(edits[i])
                i += 1
            equals = 0
            while equals <= 2 and i < len(edits):
                if edits[i].type == " ":
                    equals += 1
                else:
                    equals = 0
                hunk.edits.append(edits[i])
                i += 1
            hunks.append(hunk)

        return hunks
