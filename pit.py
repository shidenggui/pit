import argparse
import os
import subprocess
import sys

from pit.commands.add import AddCommand
from pit.commands.branch import BranchCommand
from pit.commands.checkout import CheckoutCommand
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
    commit_cmd.add_argument('-m', '--message', help="commit message", default='')

    add_cmd = subparsers.add_parser("add", help="add help")
    add_cmd.set_defaults(cmd="add")
    add_cmd.add_argument('files', nargs='+')

    status_cmd = subparsers.add_parser("status", help="status help")
    status_cmd.set_defaults(cmd="status")
    status_cmd.add_argument('--porcelain', action="store_true")

    diff_cmd = subparsers.add_parser("diff", help="diff help")
    diff_cmd.set_defaults(cmd="diff")
    diff_cmd.add_argument('--cached', action="store_true")

    branch_cmd = subparsers.add_parser("branch", help="branch help")
    branch_cmd.set_defaults(cmd="branch")
    branch_cmd.add_argument('name', nargs='?')
    branch_cmd.add_argument('revision', nargs='?', default=None)
    branch_cmd.add_argument('-D', '--delete', action='store_true')
    branch_cmd.add_argument('-v', '--verbose', action='store_true')

    checkout_cmd = subparsers.add_parser("checkout", help="checkout help")
    checkout_cmd.set_defaults(cmd="checkout")
    checkout_cmd.add_argument('revision', nargs='?', default=None)

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
                          commit_msg=args.message).run()
        case "add":
            AddCommand(root_dir, paths=args.files).run()
        case "status":
            StatusCommand(root_dir, porcelain=args.porcelain).run()
        case "diff":
            with pager():
                DiffCommand(root_dir, cached=args.cached).run()
        case "branch":
            BranchCommand(root_dir, name=args.name, revision=args.revision, delete=args.delete, verbose=args.verbose).run()
        case "checkout":
            CheckoutCommand(root_dir, revision=args.revision).run()
        case _:
            print('Unsupported command: ', args.cmd)


if __name__ == "__main__":
    entrypoint()
