from pprint import pprint

from pit.commands.base import BaseCommand
from pit.exceptions import CheckoutConflict
from pit.migration import Migration
from pit.revesion import Revision
from pit.tree_diff import TreeDiff


class CheckoutCommand(BaseCommand):
    def __init__(self, root_dir: str, *, revision: str):
        super().__init__(root_dir)
        self.revision = revision

    def run(self):
        head = self.repo.refs.read_head()
        before_commit = self.repo.database.load(head)

        oid = Revision.resolve(self.revision, repo=self.repo)
        after_commit = self.repo.database.load(oid)

        diff = TreeDiff.diff(
            before_commit.tree_oid, after_commit.tree_oid, repo=self.repo
        )
        try:
            Migration(self.repo).apply(diff)
        except CheckoutConflict as e:
            print(e)
            return

        if self.revision in self.repo.refs.list_branches():
            self.repo.refs.update_head(branch=self.revision)
        else:
            self.repo.refs.update_head(oid=after_commit.oid)
