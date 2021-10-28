import argparse
import os
import time
from pathlib import Path

from pit.database import Database
from pit.git_object import Blob, Tree, Entry, Commit
from pit.refs import Refs


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

            entries = []
            for file in Path(cwd).iterdir():
                if file.name == ".git":
                    continue
                if file.is_dir():
                    print(f"Skip dir {file.name} because not supported")
                    continue
                blob = Blob(content=file.read_bytes())
                entries.append(Entry(oid=blob.oid, name=file.name))
                database.store(blob)
            tree = Tree(entries=entries)
            database.store(tree)
            commit = Commit(
                tree_oid=tree.oid,
                timestamp=int(time.time()),
                timezone="+0800",
                user_name=author_name,
                user_email=author_email,
                message=commit_msg,
            )
            database.store(commit)
            refs.update_head(commit.oid)
        case _:
            pass


if __name__ == "__main__":
    entrypoint()
