import os
import time
from collections import defaultdict
from pathlib import Path

from pit.commands.base import BaseCommand
from pit.git_object import Tree, TreeEntry, Commit
from pit.index import IndexEntry
from pit.values import GitFileMode, AuthorSign


class CommitCommand(BaseCommand):
    def __init__(
        self, root_dir: str, *, author_name: str, author_email: str, commit_msg: str
    ):
        super().__init__(root_dir)
        self.author_name = author_name
        self.author_email = author_email
        self.commit_msg = commit_msg

    def run(self):
        # construct index tree
        index_tree: dict[str, defaultdict | IndexEntry] = defaultdict(
            lambda: defaultdict(dict)
        )

        def construct_tree(index_entry: IndexEntry):
            path = Path(index_entry.file_path)

            tree = index_tree
            for part in path.parent.parts:
                tree = tree[part]
            tree[path.name] = index_entry

        for index_entry in self.repo.index.entries.values():
            construct_tree(index_entry)

        # save git tree object
        trees = []

        def construct_tree_object(
            root: dict[str, dict | IndexEntry],
            tree: Tree | None,
            parents: list[str],
        ):
            if isinstance(root, IndexEntry):
                tree.entries.append(root.to_tree_entry())
                return tree

            sub_tree = Tree(entries=[])
            for part in root:
                construct_tree_object(root[part], sub_tree, parents=[*parents, part])
            # Save later for same tree detection when implementing "nothing to commit, working tree clean"
            trees.append(sub_tree)
            tree.entries.append(
                TreeEntry(
                    oid=sub_tree.oid,
                    path=os.path.join(*parents),
                    mode=GitFileMode.dir(),
                )
            )
            return tree

        root_tree = construct_tree_object(index_tree, Tree(entries=[]), parents=[""])
        tree_oid = root_tree.entries[0].oid
        if (
            self.repo.database.has_exists(tree_oid)
            # Also diff from the previous commit's tree oid
            and self.repo.refs.read_head()
            and self.repo.database.load(self.repo.refs.read_head()).tree_oid == tree_oid
        ):
            print("nothing to commit, working tree clean")
            return

        for tree in trees:
            self.repo.database.store(tree)

        commit = Commit(
            tree_oid=tree_oid,
            author=AuthorSign(
                name=self.author_name,
                email=self.author_email,
                timestamp=int(time.time()),
                timezone="+0800",
            ),
            message=self.commit_msg,
            parent_oid=self.repo.refs.read_head(),
        )
        self.repo.database.store(commit)
        self.repo.refs.update_ref_head(commit.oid)
