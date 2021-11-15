from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
import zlib
from typing import Type

from pit.git_object import GitObject, Tree, Commit, Blob
from pit.index import Index


@dataclass
class ObjectPath:
    oid: str
    root_dir: Path

    @cached_property
    def path(self) -> Path:
        return self.root_dir / ".git/objects" / self.oid[:2] / self.oid[2:]

    def load(self) -> GitObject:
        raw = zlib.decompress(self.path.read_bytes())
        match raw.split(b' ')[0]:
            case b'tree':
                return Tree.from_raw(raw)
            case b'commit':
                return Commit.from_raw(raw)
            case b'blob':
                return Blob.from_raw(raw)
            case _:
                raise NotImplementedError



class Database:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.git_dir = self.root_dir / ".git"
        self.objects_dir = self.git_dir / "objects"
        self.index_path = self.git_dir / "index"

    def init(self):
        self.objects_dir.mkdir(parents=True, exist_ok=True)

    def has_exists(self, object_id: str) -> bool:
        return ObjectPath(object_id, self.root_dir).path.exists()

    def store(self, obj: GitObject):
        object_path = ObjectPath(obj.oid, self.root_dir).path
        if object_path.exists():
            return
        object_path.parent.mkdir(parents=True, exist_ok=True)
        object_path.write_bytes(zlib.compress(bytes(obj)))

    def load(self, object_id: str) -> GitObject:
        object_id = ObjectPath(object_id, self.root_dir)
        return object_id.load()

    def store_index(self, index: Index):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_bytes(bytes(index))
