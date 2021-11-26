import datetime
from collections import defaultdict
from functools import cached_property

from pit.commands.base import BaseCommand
from pit.constants import Color
from pit.git_object import Commit
from pit.values import ObjectId


class LogCommand(BaseCommand):
    def __init__(self, root_dir: str, *, oneline: bool):
        super().__init__(root_dir)
        self.oneline = oneline

    @cached_property
    def head(self):
        return self.repo.refs.read_head()

    @cached_property
    def oid2branches(self) -> dict[str, list[str]]:
        oid2branch = defaultdict(list)

        for branch in self.repo.refs.list_branches():
            oid2branch[self.repo.refs.read_branch(branch)].append(branch)
        return oid2branch

    def run(self):
        if not self.head:
            return

        for commit in self._find_parent(self.head):
            self._show_commit(commit)

    def _show_commit(self, commit: Commit):
        decoration = self._generate_decoration(commit.oid)
        if self.oneline:
            self._show_oneline(commit, decoration)
        else:
            self._show_medium(commit, decoration)

    def _generate_decoration(self, oid: str) -> str:
        branches = self.oid2branches.get(oid)
        if not branches:
            return ""

        coloreds = []
        for branch in branches:
            colored = f"{Color.GREEN}{Color.BOLD}{branch}{Color.RESET_ALL}"
            coloreds.append(colored)
        joined_branches = ", ".join(coloreds)
        if self.head == oid:
            joined_branches = (
                f"{Color.CYAN}{Color.BOLD}HEAD -> {Color.RESET_ALL}{joined_branches}"
            )
        return f"{Color.YELLOW}({Color.RESET_ALL}{joined_branches}{Color.YELLOW}){Color.RESET_ALL} "

    def _show_medium(self, commit: Commit, decoration: str):
        message = "\n    ".join(commit.message.split("\n"))
        print(
            f"""{Color.YELLOW}commit {commit.oid}{Color.RESET_ALL} {decoration}
Author: {commit.author.name} <{commit.author.email}>
Date:   {datetime.datetime.fromtimestamp(commit.author.timestamp).strftime("%a %b %d %H:%M:%S %Y")} {commit.author.timezone}

    {message}
"""
        )

    def _show_oneline(self, commit: Commit, decoration: str):
        print(
            f"""{Color.YELLOW}{ObjectId(commit.oid).short_id}{Color.RESET_ALL} {decoration}{commit.title}"""
        )

    def _find_parent(self, parent: str):
        commit: Commit = self.repo.database.load(parent)
        yield commit
        if commit.parent_oid:
            yield from self._find_parent(commit.parent_oid)
