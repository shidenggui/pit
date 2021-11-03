import os
import time
from pathlib import Path
from typing import List

from pit.constants import IGNORE
from pit.database import Database
from pit.git_object import Blob, Entry, Commit, Tree
from pit.index import Index
from pit.refs import Refs
from pit.values import Author


class Workspace:
    @classmethod
    def init(cls):
        cwd = os.getcwd()
        database = Database(cwd)
        refs = Refs(cwd)

        database.init()
        refs.init()

    @classmethod
    def commit(cls, *, author_name: str, author_email: str, commit_msg: str):
        cwd = os.getcwd()
        database = Database(cwd)
        refs = Refs(cwd)

        def walk_dir(root: Path, entries: list):
            if root.name in IGNORE:
                return entries

            if root.is_file():
                blob = Blob(content=root.read_bytes())
                database.store(blob)

                entries.append(Entry(oid=blob.oid, path=str(root)))
                return entries

            sub_entries = []
            for path in root.iterdir():
                walk_dir(path, sub_entries)
            if sub_entries:
                tree = Tree(entries=sub_entries)
                database.store(tree)

                entries.append(Entry(oid=tree.oid, path=str(root)))
            return entries

        tree_entry = walk_dir(Path(cwd), [])[0]
        commit = Commit(
            tree_oid=tree_entry.oid,
            author=Author(
                name=author_name,
                email=author_email,
                timestamp=int(time.time()),
                timezone="+0800",
            ),
            message=commit_msg,
            parent_oid=refs.read_head(),
        )
        database.store(commit)
        refs.update_head(commit.oid)

    @classmethod
    def add(cls, files: List[str]):
        if not files:
            return
        cwd = os.getcwd()

        database = Database(cwd)
        index = Index(cwd)
        for file in files:
            index.add_file(file)
        database.store_index(index)
