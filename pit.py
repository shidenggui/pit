import argparse
import os

from pit.commands.add import AddCommand
from pit.commands.commit import CommitCommand
from pit.commands.init import InitCommand


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
        case _:
            pass


if __name__ == "__main__":
    entrypoint()
