import os
from pathlib import Path

from pit.exceptions import CheckoutConflict
from pit.git_object import TreeEntry
from pit.index import IndexEntry
from pit.repository import Repository
from pit.tree_diff import TreeDiff, Added, Deleted, Updated


class Migration:
    def __init__(self, repo: Repository):
        self.repo = repo

    def apply(self, tree_diff: dict[str, Added | Deleted | Updated]):
        conflicts = []
        added = {}
        deleted = {}
        updated = {}
        for path, diff in tree_diff.items():
            path = Path(path)
            match diff:
                case Added():
                    if path.exists():
                        conflicts.append(str(path))
                    else:
                        added[path] = diff
                case Deleted():
                    if self._detect_deleted_conflict(path, diff):
                        conflicts.append(str(path))
                    else:
                        deleted[path] = diff
                case Updated():
                    if self._detect_updated_conflict(path, diff):
                        conflicts.append(str(path))
                    else:
                        updated[path] = diff
                case _:
                    pass
        if conflicts:
            raise CheckoutConflict(conflicts)

        # delete first
        for path, diff in deleted.items():
            path.unlink(missing_ok=True)
            self.repo.index.remove_file(path)
            if not any(os.scandir(path.parent)):
                path.parent.rmdir()

        for path, diff in added.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(self.repo.database.load(diff.entry.oid).content)
            self.repo.index.add_file(path)
        for path, diff in updated.items():
            path.write_bytes(self.repo.database.load(diff.after.oid).content)
            path.chmod(diff.after.mode)
            self.repo.index.add_file(path)

        self.repo.database.store_index(self.repo.index)

    def _detect_deleted_conflict(self, path: Path, deleted: Deleted):
        if not path.exists():
            return True
        current = IndexEntry.from_file(path).to_tree_entry()
        if (current.mode != deleted.entry.mode
                or current.oid != deleted.entry.oid
        ):
            return True
        return False

    def _detect_updated_conflict(self, path: Path, updated: Updated):
        if not path.exists():
            return True
        current = IndexEntry.from_file(path).to_tree_entry()
        if current.mode != updated.before.mode or current.oid != updated.before.oid:
            return True
        return False
