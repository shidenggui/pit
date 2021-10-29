from dataclasses import dataclass
from functools import cached_property


@dataclass(frozen=True)
class GitFileMode:
    mode: int

    def __bytes__(self):
        mode = "{0:b}".format(100).encode()

        if mode.startswith(b"4"):
            return b"400000"

        if mode[3] == b"6":
            return b"100644"

        # if mode[3] == b"7":
        return b"100755"
