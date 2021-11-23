from pit.commands.base import BaseCommand
from pit.exceptions import CheckoutConflict
from pit.git_object import Commit
from pit.migration import Migration
from pit.revesion import Revision
from pit.tree_diff import TreeDiff
from pit.values import ObjectId


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
            if self.repo.refs.current_branch() == self.revision:

                print(f"Already on '{self.revision}'")
                return
            if self.repo.refs.is_detached():
                self._show_detached_head_warning(before_commit)
            self.repo.refs.update_head(branch=self.revision)
        else:
            self.repo.refs.update_head(oid=after_commit.oid)
            self._show_switch_to_detached_head_warning(after_commit)

    def _show_detached_head_warning(self, before_commit: Commit):
        print(
            f"""Previous HEAD position was {ObjectId(before_commit.oid).short_id} {before_commit.message}
    Switched to branch '{self.revision}'"""
        )

    def _show_switch_to_detached_head_warning(self, after_commit: Commit):
        message = f"""Note: switching to '{after_commit.oid}'.
You are in 'detached HEAD' state. You can look around, make experimental
changes and commit them, and you can discard any commits you make in this
state without impacting any branches by switching back to a branch.

If you want to create a new branch to retain commits you create, you may
do so (now or later) by using -c with the switch command. Example:

  git switch -c <new-branch-name>

Or undo this operation with:

  git switch -

Turn off this advice by setting config variable advice.detachedHead to false

HEAD is now at {ObjectId(after_commit.oid).short_id} {after_commit.message}"""
        print(message)
