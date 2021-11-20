from dataclasses import dataclass
from pathlib import Path

from pit.git_object import TreeEntry
from pit.repository import Repository


@dataclass
class Added:
    entry: TreeEntry


@dataclass
class Deleted:
    entry: TreeEntry


@dataclass
class Updated:
    before: TreeEntry
    after: TreeEntry


class TreeDiff:
    """Diff between two commits"""

    @classmethod
    def diff(
        cls, before: str, after: str, *, repo: Repository
    ) -> dict[str, (TreeEntry, TreeEntry)]:
        return {
            str(path): entry
            for path, entry in cls._diff(
                before, after, parent=Path(""), repo=repo
            ).items()
        }

    @classmethod
    def _diff(
        cls,
        before: str | None,
        after: str | None,
        parent: Path,
        repo: Repository,
    ) -> dict[Path, (TreeEntry, TreeEntry)]:
        before = repo.database.load(before) if before else None
        after = repo.database.load(after) if after else None

        before_children = (
            {child.path: child for child in before.entries} if before else {}
        )
        after_children = {child.path: child for child in after.entries} if after else {}

        changes = {}
        for added in set(after_children) - set(before_children):
            added_child = after_children[added]
            if added_child.is_dir():
                changes.update(cls._diff(None, added_child.oid, parent / added, repo))
            else:
                changes[parent / added] = Added(added_child)
        for deleted in set(before_children) - set(after_children):
            deleted_child = before_children[deleted]
            if deleted_child.is_dir():
                changes.update(
                    cls._diff(deleted_child.oid, None, parent / deleted, repo)
                )
            else:
                changes[parent / deleted] = Deleted(deleted_child)

        modified = [
            child
            for child in set(before_children) & set(after_children)
            if before_children[child] != after_children[child]
        ]
        for changed in modified:
            before_child, after_child = (
                before_children[changed],
                after_children[changed],
            )
            if not before_child.is_dir() and not after_child.is_dir():
                changes[parent / changed] = Updated(
                    before_child,
                    after_child,
                )
            elif before_child.is_dir() and after_child.is_dir():
                changes.update(
                    cls._diff(
                        before_child.oid,
                        after_child.oid,
                        parent / before_child.path,
                        repo,
                    )
                )
            elif before_child.is_dir():
                changes[parent / changed] = Added(after_child)
                changes.update(
                    cls._diff(
                        before_child.oid,
                        None,
                        parent / before_child.path,
                        repo,
                    )
                )
            else:
                changes[parent / changed] = Deleted(after_child)
                changes.update(
                    cls._diff(
                        None,
                        after_child.oid,
                        parent / after_child.path,
                        repo,
                    )
                )
        return changes
