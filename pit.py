import argparse
import os
import subprocess
import sys

from pit.commands.add import AddCommand
from pit.commands.commit import CommitCommand
from pit.commands.diff import DiffCommand
from pit.commands.init import InitCommand
from pit.commands.status import StatusCommand
from pit.pager import pager


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

    add_cmd = subparsers.add_parser("add", help="add help")
    add_cmd.set_defaults(cmd="add")
    add_cmd.add_argument('files', nargs='+')

    status_cmd = subparsers.add_parser("status", help="status help")
    status_cmd.set_defaults(cmd="status")
    status_cmd.add_argument('--porcelain', action="store_true")

    diff_cmd = subparsers.add_parser("diff", help="diff help")
    diff_cmd.set_defaults(cmd="diff")
    diff_cmd.add_argument('--cached', action="store_true")

    return parser


def entrypoint():
    args = generate_parser().parse_args()
    root_dir = os.getcwd()
    match args.cmd:
        case "init":
            InitCommand(root_dir).run()
        case "commit":
            CommitCommand(root_dir,
                          author_name=os.getenv("GIT_AUTHOR_NAME"),
                          author_email=os.getenv("GIT_AUTHOR_EMAIL"),
                          commit_msg=args.m).run()
        case "add":
            AddCommand(root_dir, paths=args.files).run()
        case "status":
            StatusCommand(root_dir, porcelain=args.porcelain).run()
        case "diff":
            with pager():
                DiffCommand(root_dir, cached=args.cached).run()
        case _:
            pass


if __name__ == "__main__":
    entrypoint()
