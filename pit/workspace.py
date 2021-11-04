import os
import time
from collections import defaultdict
from pathlib import Path
from typing import List, Optional

from pit.constants import IGNORE
from pit.database import Database
from pit.git_object import TreeEntry, Commit, Tree
from pit.index import Index, IndexEntry
from pit.refs import Refs
from pit.repository import Repository
from pit.values import Author, GitFileMode


class Workspace:
    @classmethod
    def init(cls):
        repo = Repository(os.getcwd())
        repo.database.init()
        repo.refs.init()

    @classmethod
    def commit(cls, *, author_name: str, author_email: str, commit_msg: str):
        repo = Repository(os.getcwd())

        # construct_tree
        index_tree: dict[str, defaultdict | IndexEntry] = defaultdict(
            lambda: defaultdict(dict)
        )

        def construct_tree(index_entry: IndexEntry):
            path = Path(index_entry.file_path)

            tree = index_tree
            for part in path.parent.parts:
                tree = tree[part]
            tree[path.name] = index_entry

        for index_entry in repo.index.entries.values():
            construct_tree(index_entry)

        # save tree
        def construct_tree_object(
            root: dict[str, dict | IndexEntry],
            tree: Optional[Tree],
            parents: list[str],
        ):
            if isinstance(root, IndexEntry):
                tree.entries.append(root.to_tree_entry())
                return tree

            sub_tree = Tree(entries=[])
            for part in root:
                construct_tree_object(root[part], sub_tree, parents=[*parents, part])
            repo.database.store(sub_tree)
            tree.entries.append(
                TreeEntry(
                    oid=sub_tree.oid,
                    path=os.path.join(*parents),
                    mode=GitFileMode.dir(),
                )
            )
            return tree

        tree = construct_tree_object(index_tree, Tree(entries=[]), parents=[""])
        commit = Commit(
            tree_oid=tree.entries[0].oid,
            author=Author(
                name=author_name,
                email=author_email,
                timestamp=int(time.time()),
                timezone="+0800",
            ),
            message=commit_msg,
            parent_oid=repo.refs.read_head(),
        )
        repo.database.store(commit)
        repo.refs.update_head(commit.oid)

    @classmethod
    def add(cls, paths: List[str]):
        if not paths:
            return
        for path in paths:
            path = Path(path)
            if not path.exists():
                print(f"fatal: pathspec '{path}' did not match any files")
                return

        repo = Repository(os.getcwd())

        for path in paths:
            path = Path(path)
            if path.is_dir():
                for sub_path in path.rglob("*"):
                    if any(str(sub_path).startswith(ignore) for ignore in IGNORE):
                        continue
                    if sub_path.is_file():
                        blob = repo.index.add_file(sub_path)
                        repo.database.store(blob)
            else:
                blob = repo.index.add_file(path)
                repo.database.store(blob)
        repo.index.clean()
        repo.database.store_index(repo.index)
