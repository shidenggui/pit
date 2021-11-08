from pathlib import Path

from pit.commands.base import BaseCommand
from pit.constants import IGNORE


class AddCommand(BaseCommand):
    def __init__(self, root_dir: str, *, paths: list[str]):
        super().__init__(root_dir)
        self.paths = paths
        self.ignores = [*self.repo.ignores, *IGNORE]

    def run(self):
        if not self.paths:
            return
        for path in self.paths:
            path = Path(path)
            if not path.exists():
                print(f"fatal: pathspec '{path}' did not match any files")
                return

        for path in self.paths:
            path = Path(path)
            if path.is_dir():
                for sub_path in path.rglob("*"):
                    if self._should_ignore(sub_path):
                        continue
                    if sub_path.is_file():
                        blob = self.repo.index.add_file(sub_path)
                        self.repo.database.store(blob)
            else:
                blob = self.repo.index.add_file(path)
                self.repo.database.store(blob)
        self.repo.index.clean()
        self.repo.database.store_index(self.repo.index)

    def _should_ignore(self, path: Path):
        return any(ignore in path.parts for ignore in self.ignores)