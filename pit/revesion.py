import re

from pit.exceptions import UnknownRevision, InvalidRevision
from pit.git_object import Commit
from pit.repository import Repository


class AstNode:
    pass


class Revision:
    REF_MATCH = r"[^\^\~]+"
    ANCESTOR_MATCH = r"([~\^]+)(\d*)"

    @classmethod
    def resolve(cls, revision: str, *, repo: Repository) -> str:
        ref, parents = cls._parse(revision)
        if ref.lower() in ("head", "@"):
            ref = repo.refs.read_head()
        elif ref in repo.refs.list_branches():
            ref = repo.refs.read_branch(ref)
        else:
            ref = repo.database.prefix_match(ref)

        commit = repo.database.load(ref)
        if not isinstance(commit, Commit):
            raise InvalidRevision(revision)

        for _ in range(parents):
            ref = commit.parent_oid
            if not ref:
                raise UnknownRevision(revision)

            commit = repo.database.load(ref)
            if not isinstance(commit, Commit):
                raise InvalidRevision(revision)

        return ref

    @classmethod
    def _parse(cls, expr: str) -> (str, int):
        matched = re.match(cls.REF_MATCH, expr)
        start_ref = matched.group()
        remain = expr[matched.end() :]

        parents = 0
        while remain:
            if matched := re.match(cls.ANCESTOR_MATCH, remain):
                parents += len(matched.group(1))
                if matched.group(2):
                    parents += int(matched.group(2)) - 1
                remain = remain[matched.end() :]
            else:
                raise InvalidRevision(expr)
        return start_ref, parents
