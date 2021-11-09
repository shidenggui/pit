from dataclasses import dataclass, field
from pathlib import Path

from pit.commands.base import BaseCommand
from pit.constants import IGNORE
from pit.values import GitPath


@dataclass()
class FileStatusGroup:
    root_dir: Path
    modified: set[str] = field(default_factory=set)
    added: set[str] = field(default_factory=set)
    deleted: set[str] = field(default_factory=set)

    def porcelain(self) -> str:
        lines = []
        for path in sorted(self.deleted):
            lines.append(f" D {GitPath(path, root_dir=self.root_dir)}")
        for path in sorted(self.modified):
            lines.append(f" M {GitPath(path, root_dir=self.root_dir)}")
        for path in sorted(self.added):
            lines.append(f"?? {GitPath(path, root_dir=self.root_dir)}")
        return "\n".join(lines)


class StatusCommand(BaseCommand):
    def __init__(self, root_dir: str, *, porcelain: bool):
        super().__init__(root_dir)
        self.ignores = [*self.repo.ignores, *IGNORE]
        self.porcelain = porcelain

    def run(self):
        status = FileStatusGroup(root_dir=self.root_dir)
        existed_files = set()
        for path in self.repo.root_dir.rglob("*"):
            path = path.relative_to(self.repo.root_dir)
            existed_files.add(str(path))
            if self._should_ignore(path):
                continue
            if path.is_dir():
                continue
            if self.repo.index.has_tracked(path):
                if self.repo.index.has_modified(path):
                    status.modified.add(str(path))
                continue

            if len(path.parts) == 1:
                status.added.add(str(path))
            else:
                for parent in reversed(path.parents[:-1]):
                    if str(parent) in status.added:
                        break
                    if not self.repo.index.has_tracked(parent):
                        status.added.add(str(parent))
                        break
                else:
                    status.added.add(str(path))
        for index_file in self.repo.index.entries:
            if index_file not in existed_files:
                status.deleted.add(index_file)
        print(status.porcelain())

    def _should_ignore(self, path: Path):
        return any(ignore in path.parts for ignore in self.ignores)
