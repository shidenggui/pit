import os
import subprocess
import sys
from pit.database import Database
from pit.diff import Diff
from pit.hunk import Hunk
    DELETED_PATH = "/dev/null"
    DELETED_OID = "0" * 40
    data: bytes
    def from_index_entry(
        cls, index_entry: IndexEntry, database: Database
    ) -> "DiffEntry":
        # noinspection PyUnresolvedReferences
        data = (
            database.load(index_entry.oid).content
            if database.has_exists(index_entry.oid)
            else Path(index_entry.file_path).read_bytes()
        )
            data=data,
    def from_tree_entry(cls, tree_entry: TreeEntry, database: Database) -> "DiffEntry":
        # noinspection PyUnresolvedReferences
            data=database.load(tree_entry.oid).content,
        return DiffEntry(
            file_path=cls.DELETED_PATH, mode="", oid=cls.DELETED_OID, data=b""
        )
        return self.file_path != self.DELETED_PATH
    def display(self):

        color_prefix = f'{Color.WHITE}{Color.BOLD}'
        print(f"{color_prefix}diff --git a/{a_file_path} b/{b_file_path}")
            print(f"{color_prefix}old mode: ", self.a_file.mode)
            print(f"{color_prefix}new mode: ", self.b_file.mode, Color.RESET_ALL)
            print(f"{color_prefix}new file mode", self.b_file.mode)
            print(f"{color_prefix}deleted file mode", self.a_file.mode)
            f"{color_prefix}index {self.a_file.short_oid}..{self.b_file.short_oid} {self.a_file.mode if self.b_file.exists else ''}"
        print(f"{color_prefix}--- {'a/' if self.a_file.exists else ''}{self.a_file.file_path}")
            f"{color_prefix}+++ {'b/' if self.b_file.exists else ''}{self.b_file.file_path}{Color.RESET_ALL}"
        for hunk in Hunk.filters(Diff.from_lines(self.a_file.data, self.b_file.data).diff()):
            print(hunk.header())
            for edit in hunk.edits:
                print(edit)
                a_file=DiffEntry.from_tree_entry(head_entry, self.repo.database)
                b_file=DiffEntry.from_index_entry(index_entry, self.repo.database)
            ).display()
                a_file=DiffEntry.from_index_entry(index_entry, self.repo.database),
                b_file=DiffEntry.from_index_entry(workspace_entry, self.repo.database)
            ).display()