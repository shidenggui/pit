from dataclasses import dataclass
from functools import cached_property


@dataclass(frozen=True)
class GitFileMode:
    mode: int

    def __bytes__(self):
        mode = "{0:o}".format(self.mode)

        if mode.startswith("4"):
            return b"040000"

        if mode[3] == "6":
            return b"100644"

        # if mode[3] == b"7":
        return b"100755"


@dataclass(frozen=True)
class Author:
    name: str
    email: str
    timestamp: int
    timezone: str

    def __bytes__(self):
        return b"%s <%s> %d %s" % (
            self.name.encode(),
            self.email.encode(),
            self.timestamp,
            self.timezone.encode(),
        )
