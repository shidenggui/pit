from pathlib import Path

from pit.commands.base import BaseCommand
from pit.constants import IGNORE


class StatusCommand(BaseCommand):
    def __init__(self, root_dir: str, *, porcelain: bool):
        super().__init__(root_dir)
        self.ignores = [*self.repo.ignores, *IGNORE]
        self.porcelain = porcelain

    def run(self):
        status = set()
        for path in self.repo.root_dir.rglob("*"):
            path = path.relative_to(self.repo.root_dir)
            if self._should_ignore(path):
                continue
            if path.is_dir():
                continue
            if self.repo.index.tracked(path):
                continue
            if len(path.parts) == 1:
                status.add(str(path))
            else:
                for parent in reversed(path.parents[:-1]):
                    if str(parent) in status:
                        break
                    if not self.repo.index.tracked(parent):
                        status.add(str(parent))
                        break
                else:
                    status.add(str(path))
        for path in sorted(status):
            relative_path = Path(path).resolve().relative_to(self.root_dir)
            print(
                f"?? {relative_path if relative_path.is_file() else f'{relative_path}/'}"
            )

    def _should_ignore(self, path: Path):
        return any(ignore in path.parts for ignore in self.ignores)
