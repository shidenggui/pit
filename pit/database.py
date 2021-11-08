from pathlib import Path
import zlib

from pit.git_object import GitObject
from pit.index import Index


class Database:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.git_dir = self.root_dir / ".git"
        self.objects_dir = self.git_dir / "objects"
        self.index_path = self.git_dir / "index"

    def init(self):
        self.objects_dir.mkdir(parents=True, exist_ok=True)

    def has_exists(self, object_id: str) -> bool:
        return (self.objects_dir / object_id[:2] / object_id[2:]).exists()

    def store(self, obj: GitObject):
        path = self.objects_dir / obj.oid[:2] / obj.oid[2:]
        if path.exists():
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(zlib.compress(obj.saved))

    def store_index(self, index: Index):
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.index_path.write_bytes(bytes(index))
