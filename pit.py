import argparse
import os
import time
from pathlib import Path

from pit.constants import IGNORE
from pit.database import Database
from pit.git_object import Blob, Tree, Entry, Commit
from pit.refs import Refs
from pit.values import Author


def generate_parser():
    """
    >>> parser = generate_parser()
    >>> parser.parse_args(['add', '--all'])
    Namespace(all=True, cmd='add')

    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help="sub-command help")

    init_cmd = subparsers.add_parser("init", help="init project")
    init_cmd.set_defaults(cmd="init")

    commit_cmd = subparsers.add_parser("commit", help="commit help")
    commit_cmd.set_defaults(cmd="commit")
    commit_cmd.add_argument('-m', help="commit message", default='')

    return parser


def entrypoint():
    args = generate_parser().parse_args()
    match args.cmd:
        case "init":
            cwd = os.getcwd()
            database = Database(cwd)
            refs = Refs(cwd)

            database.init()
            refs.init()
        case "commit":
            author_name = os.getenv("GIT_AUTHOR_NAME")
            author_email = os.getenv("GIT_AUTHOR_EMAIL")
            commit_msg = args.m

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
                parent_oid=refs.read_head()
            )
            database.store(commit)
            refs.update_head(commit.oid)
        case _:
            pass


if __name__ == "__main__":
    entrypoint()
