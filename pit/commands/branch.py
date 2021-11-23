from pit.constants import Color
from pit.exceptions import (
    InvalidBranchName,
    BranchAlreadyExists,
    InvalidRevision,
    UnknownRevision,
)
from pit.commands.base import BaseCommand
from pit.pager import pager
from pit.revesion import Revision
from pit.values import ObjectId


class BranchCommand(BaseCommand):
    def __init__(
        self,
        root_dir: str,
        *,
        name: str,
        revision: str,
        delete: bool = False,
        verbose: bool = False,
    ):
        super().__init__(root_dir)
        self.name = name
        self.revision = revision
        self.delete = delete
        self.verbose = verbose

    def run(self):
        if self.delete:
            self._delete_branch()
            return

        if not self.name and not self.revision:
            with pager():
                self._list_branches()
            return

        try:
            if self.revision:
                oid = Revision.resolve(self.revision, repo=self.repo)
            else:
                oid = self.repo.refs.read_head()
            self.repo.refs.create_branch(self.name, oid)
        except (
            InvalidBranchName,
            BranchAlreadyExists,
            InvalidRevision,
            UnknownRevision,
        ) as e:
            print(e)

    def _list_branches(self):
        current_branch = self.repo.refs.current_branch()
        for branch in self.repo.refs.list_branches():
            verbose = ""
            if self.verbose:
                commit = self.repo.database.load(self.repo.refs.read_branch(branch))
                verbose = f"{ObjectId(commit.oid).short_id} {commit.message}"

            if branch == current_branch:
                print(f"* {Color.GREEN}{branch}{Color.RESET_ALL} {verbose}")
            else:
                print(f"  {branch} {verbose}")

    def _delete_branch(self):
        if not self.name:
            print("fatal: branch name required")
            return

        if self.name not in self.repo.refs.list_branches():
            print(f"error: branch '{self.name}' not found.")
            return

        self.repo.refs.delete_branch(self.name)
