from functools import cached_property

from pit.database import Database
from pit.index import Index
from pit.refs import Refs


class Repository:
    def __init__(self, root_dir: str):
        self.work_dir = root_dir

    @cached_property
    def index(self):
        return Index(self.work_dir)

    @cached_property
    def database(self):
        return Database(self.work_dir)

    @cached_property
    def refs(self):
        return Refs(self.work_dir)
