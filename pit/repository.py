from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from pit.constants import IGNORE
from pit.database import Database
from pit.git_object import Commit, Tree, TreeEntry
from pit.index import Index
from pit.refs import Refs
from pit.values import GitFileMode


@dataclass()
class FileStatusGroup:
    root_dir: Path
    head_tree: dict[str, TreeEntry] = field(default_factory=dict)
    workspace_modified: set[str] = field(default_factory=set)
    workspace_added: set[str] = field(default_factory=set)
    workspace_deleted: set[str] = field(default_factory=set)

    index_modified: set[str] = field(default_factory=set)
    index_added: set[str] = field(default_factory=set)
    index_deleted: set[str] = field(default_factory=set)


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

    @cached_property
    def status(self) -> FileStatusGroup:
        status = FileStatusGroup(root_dir=self.root_dir)

        # check workspace / index differences
        existed_files = set()
        for path in self.root_dir.rglob("*"):
            path = path.relative_to(self.root_dir)
            existed_files.add(str(path))
            if any(ignore in path.parts for ignore in self.ignores):
                continue
            if path.is_dir():
                continue
            if self.index.has_tracked(path):
                if self.index.has_modified(path):
                    status.workspace_modified.add(str(path))
                continue

            if len(path.parts) == 1:
                status.workspace_added.add(str(path))
            else:
                for parent in reversed(path.parents[:-1]):
                    if str(parent) in status.workspace_added:
                        break
                    if not self.index.has_tracked(parent):
                        status.workspace_added.add(str(parent))
                        break
                else:
                    status.workspace_added.add(str(path))
        for index_file in self.index.entries:
            if index_file not in existed_files:
                status.workspace_deleted.add(index_file)

        # check index / commit differences
        # noinspection PyTypeChecker
        commit: Commit = self.database.load(self.refs.read_head())
        # noinspection PyTypeChecker
        tree: Tree = self.database.load(commit.tree_oid)

        def flatten_tree(
            tree_entries: list[TreeEntry], parent: str = None
        ) -> list[TreeEntry]:
            flatten = []
            for entry in tree_entries:
                entry_path = f"{parent}/{entry.path}" if parent else entry.path
                if GitFileMode(entry.mode).is_file():
                    entry.path = entry_path
                    flatten.append(entry)
                    continue
                # noinspection PyTypeChecker
                sub_tree: Tree = self.database.load(entry.oid)
                flatten.extend(
                    flatten_tree(
                        sub_tree.entries,
                        parent=entry_path,
                    )
                )
            return flatten

        flatten_entries = flatten_tree(tree.entries)
        commit_entries: dict[str, TreeEntry] = {e.path: e for e in flatten_entries}
        status.head_tree = commit_entries

        for entry_path, index_entry in self.index.entries.items():
            commit_entry = commit_entries.get(entry_path)
            if not commit_entry:
                status.index_added.add(entry_path)
                continue
            if (
                index_entry.file_hash.hex() != commit_entry.oid
                or index_entry.mode != commit_entry.mode
            ):
                status.index_modified.add(entry_path)
                continue
        for entry_path in commit_entries.keys():
            if entry_path not in self.index.entries:
                status.index_deleted.add(entry_path)
        return status
