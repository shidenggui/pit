from pit.commands.base import BaseCommand


class InitCommand(BaseCommand):
    def run(self):
        self.repo.database.init()
        self.repo.refs.init()
