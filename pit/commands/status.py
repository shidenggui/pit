from pathlib import Path

from pit.commands.base import BaseCommand
from pit.constants import IGNORE
from pit.values import GitPath


class StatusCommand(BaseCommand):
    def __init__(self, root_dir: str, *, porcelain: bool):
        super().__init__(root_dir)
        self.ignores = [*self.repo.ignores, *IGNORE]
        self.porcelain = porcelain

    def run(self):
        added = set()
        modified = set()
        for path in self.repo.root_dir.rglob("*"):
            path = path.relative_to(self.repo.root_dir)
            if self._should_ignore(path):
                continue
            if path.is_dir():
                continue
            if self.repo.index.has_tracked(path):
                if self.repo.index.has_modified(path):
                    modified.add(str(path))
                continue

            if len(path.parts) == 1:
                added.add(str(path))
            else:
                for parent in reversed(path.parents[:-1]):
                    if str(parent) in added:
                        break
                    if not self.repo.index.has_tracked(parent):
                        added.add(str(parent))
                        break
                else:
                    added.add(str(path))
        for path in sorted(modified):
            print(f" M {GitPath(path, root_dir=self.root_dir)}")
        for path in sorted(added):
            print(f"?? {GitPath(path, root_dir=self.root_dir)}")

    def _should_ignore(self, path: Path):
        return any(ignore in path.parts for ignore in self.ignores)
