from pathlib import Path

from pit.repository import Repository


class BaseCommand:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.repo = Repository(root_dir)

    def run(self):
        raise NotImplementedError

