import argparse
import os
import time
from pathlib import Path

from pit.constants import IGNORE
from pit.database import Database
from pit.git_object import Blob, Tree, Entry, Commit
from pit.refs import Refs
from pit.values import Author
from pit.workspace import Workspace


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
            Workspace.init()
        case "commit":
            author_name = os.getenv("GIT_AUTHOR_NAME")
            author_email = os.getenv("GIT_AUTHOR_EMAIL")
            commit_msg = args.m
            Workspace.commit(
                author_name=author_name, author_email=author_email, commit_msg=commit_msg
            )
        case _:
            pass


if __name__ == "__main__":
    entrypoint()
