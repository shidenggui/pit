from functools import cached_property
from pathlib import Path

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
        git_ignores = Path(self.root_dir) / ".gitignore"
        if not git_ignores.exists():
            return [".git"]
        return [str(p).strip() for p in git_ignores.read_text().split("\n") if p]
