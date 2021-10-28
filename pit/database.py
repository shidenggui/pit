from pathlib import Path
import zlib

from pit.git_object import GitObject


class Database:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.git_dir = self.root_dir / ".git"
        self.objects_dir = self.git_dir / "objects"

    def init(self):
        self.objects_dir.mkdir(parents=True, exist_ok=True)

    def store(self, obj: GitObject):
        path = self.objects_dir / obj.oid[:2] / obj.oid[2:]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(zlib.compress(obj.saved))
