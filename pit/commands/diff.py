from dataclasses import dataclass
from pathlib import Path

from pit.commands.base import BaseCommand
from pit.constants import Color
from pit.database import Database
from pit.diff import Diff
from pit.git_object import TreeEntry
from pit.index import IndexEntry
from pit.values import ObjectId, GitFileMode


@dataclass()
class DiffEntry:
    DELETED_PATH = "/dev/null"
    DELETED_OID = "0" * 40
    file_path: str
    mode: str
    oid: str
    data: bytes

    @classmethod
    def from_index_entry(
        cls, index_entry: IndexEntry, database: Database
    ) -> "DiffEntry":
        # noinspection PyUnresolvedReferences
        data = (
            database.load(index_entry.oid).content
            if database.has_exists(index_entry.oid)
            else Path(index_entry.file_path).read_bytes()
        )
        return DiffEntry(
            file_path=index_entry.file_path,
            mode=bytes(GitFileMode(index_entry.mode)).decode(),
            oid=index_entry.oid,
            data=data,
        )

    @classmethod
    def from_tree_entry(cls, tree_entry: TreeEntry, database: Database) -> "DiffEntry":
        # noinspection PyUnresolvedReferences
        return DiffEntry(
            file_path=tree_entry.path,
            mode=bytes(GitFileMode(tree_entry.mode)).decode(),
            oid=tree_entry.oid,
            data=database.load(tree_entry.oid).content,
        )

    @classmethod
    def from_deleted(
        cls,
    ) -> "DiffEntry":
        return DiffEntry(
            file_path=cls.DELETED_PATH, mode="", oid=cls.DELETED_OID, data=b""
        )

    @property
    def short_oid(self) -> str:
        return ObjectId(self.oid).short_id

    @property
    def exists(self):
        return self.file_path != self.DELETED_PATH


@dataclass
class DiffHeader:
    a_file: DiffEntry
    b_file: DiffEntry

    def display_index_workspace_diff(self):
        a_file_path = (
            self.a_file.file_path if self.a_file.exists else self.b_file.file_path
        )
        b_file_path = (
            self.b_file.file_path if self.b_file.exists else self.a_file.file_path
        )
        print(f"{Color.WHITE}{Color.BOLD}diff --git a/{a_file_path} b/{b_file_path}")
        # only mode changed
        if self.a_file.oid == self.b_file.oid and self.a_file.mode != self.b_file.mode:
            print("old mode: ", self.a_file.mode)
            print("new mode: ", self.b_file.mode)
            return

        if not self.a_file.exists:
            print("new file mode", self.b_file.mode)
        elif not self.b_file.exists:
            print("deleted file mode", self.a_file.mode)

        print(
            f"index {self.a_file.short_oid}..{self.b_file.short_oid} {self.a_file.mode if self.b_file.exists else ''}"
        )
        print(f"--- {'a/' if self.a_file.exists else ''}{self.a_file.file_path}")
        print(
            f"+++ {'b/' if self.b_file.exists else ''}{self.b_file.file_path}{Color.RESET_ALL}"
        )
        for edit in Diff(
            self.a_file.data.split(b"\n"), self.b_file.data.split(b"\n")
        ).diff():
            print(edit)


class DiffCommand(BaseCommand):
    def __init__(self, root_dir: str, *, cached: bool):
        super().__init__(root_dir)
        self.cached = cached

    def run(self):
        if self.cached:
            self._diff_head_index()
        else:
            self._diff_index_workspace()

    def _diff_head_index(self):
        for file_path in sorted(
            self.repo.status.index_added
            | self.repo.status.index_modified
            | self.repo.status.index_deleted
        ):
            head_entry = (
                self.repo.status.head_tree[file_path]
                if file_path not in self.repo.status.index_added
                else None
            )
            index_entry = (
                self.repo.index.entries[file_path]
                if file_path not in self.repo.status.index_deleted
                else None
            )

            DiffHeader(
                a_file=DiffEntry.from_tree_entry(head_entry, self.repo.database)
                if head_entry
                else DiffEntry.from_deleted(),
                b_file=DiffEntry.from_index_entry(index_entry, self.repo.database)
                if index_entry
                else DiffEntry.from_deleted(),
            ).display_index_workspace_diff()

    def _diff_index_workspace(self):
        for file_path in sorted(
            self.repo.status.workspace_deleted | self.repo.status.workspace_modified
        ):
            index_entry = self.repo.index.entries[file_path]
            workspace_entry = (
                IndexEntry.from_file(Path(file_path))
                if file_path in self.repo.status.workspace_modified
                else None
            )

            DiffHeader(
                a_file=DiffEntry.from_index_entry(index_entry, self.repo.database),
                b_file=DiffEntry.from_index_entry(workspace_entry, self.repo.database)
                if workspace_entry
                else DiffEntry.from_deleted(),
            ).display_index_workspace_diff()
