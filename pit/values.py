from dataclasses import dataclass, InitVar
from functools import cached_property
from pathlib import Path


@dataclass(order=True)
class GitPath:
    path: str | Path
    root_dir: InitVar[str | Path]

    def __post_init__(self, root_dir: str | Path):
        self.path = Path(self.path).absolute().relative_to(Path(root_dir).absolute())

    def __str__(self):
        return f"{self.path if not self.path.exists() or self.path.is_file() else f'{self.path}/'}"


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

    def is_dir(self) -> bool:
        return bytes(self) == b"040000"

    def is_file(self) -> bool:
        return not self.is_dir()

    @classmethod
    def from_raw(cls, raw: bytes) -> "GitFileMode":
        return GitFileMode(int(raw, 8))

    @classmethod
    def dir(cls) -> int:
        return int(b"040000", 8)


@dataclass(frozen=True)
class AuthorSign:
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


@dataclass()
class ObjectId:
    object_id: str

    @cached_property
    def short_id(self):
        return self.object_id[:7]
