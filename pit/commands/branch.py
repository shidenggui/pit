from exceptions import InvalidBranchName, BranchAlreadyExists, InvalidRevision, UnknownRevision
from pit.commands.base import BaseCommand
from pit.revesion import Revision


class BranchCommand(BaseCommand):
    def __init__(self, root_dir: str, *, name: str, revision: str):
        super().__init__(root_dir)
        self.name = name
        self.revision = revision

    def run(self):
        try:
            if self.revision:
                oid = Revision.resolve(self.revision, self.repo)
            else:
                oid = self.repo.refs.read_head()
            self.repo.refs.create_branch(self.name, oid)
        except (
            InvalidBranchName,
            BranchAlreadyExists,
            InvalidRevision,
            UnknownRevision,
        ) as e:
            print(e)
