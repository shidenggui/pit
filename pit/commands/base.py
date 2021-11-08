from pit.repository import Repository


class BaseCommand:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.repo = Repository(self.root_dir)

    def run(self):
        raise NotImplementedError

