from functools import cached_property
from pathlib import Path

from pit.constants import IGNORE
from pit.database import Database
from pit.index import Index
from pit.refs import Refs


class Repository:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)

    @cached_property
    def index(self):
        return Index(self.root_dir)

    @cached_property
    def database(self):
        return Database(self.root_dir)

    @cached_property
    def refs(self):
        return Refs(self.root_dir)

    @cached_property
    def ignores(self) -> list[str]:
        ignore_file = Path(self.root_dir) / ".gitignore"
        if not ignore_file.exists():
            return [".git"]
        git_ignores = {str(p).strip() for p in ignore_file.read_text().split("\n") if p}
        return list(git_ignores | IGNORE)
