from dataclasses import dataclass, field
from pathlib import Path

from pit.commands.base import BaseCommand
from pit.constants import IGNORE
from pit.git_object import Commit, Tree, TreeEntry
from pit.values import GitPath, GitFileMode


@dataclass()
class FileStatusGroup:
    root_dir: Path
    workspace_modified: set[str] = field(default_factory=set)
    workspace_added: set[str] = field(default_factory=set)
    workspace_deleted: set[str] = field(default_factory=set)

    index_modified: set[str] = field(default_factory=set)
    index_added: set[str] = field(default_factory=set)
    index_deleted: set[str] = field(default_factory=set)

    def porcelain(self) -> str:
        lines = []
        for path in (
            self.workspace_added
            | self.workspace_modified
            | self.workspace_deleted
            | self.index_deleted
            | self.index_modified
            | self.index_added
        ):
            git_path = GitPath(path, root_dir=self.root_dir)
            lines.append(f"{self._status_code(path)} {git_path}")
        lines.sort(key=lambda x: "zz" if x[:2] == "??" else x[3:])
        return "\n".join(lines)

    def long_format(self) -> str:
        lines = []
        if self.index_added or self.index_modified or self.index_deleted:
            lines.append("Changes to be committed:")
            lines.append('  (use "git restore --staged <file>..." to unstage)')
            for path in sorted(self.index_deleted | self.index_modified | self.index_added):
                git_path = GitPath(path, root_dir=self.root_dir)
                lines.append(f"\t\x1b[7;30;42m{self._status_txt(path)}   {git_path}\x1b[0m")

        if self.workspace_deleted or self.workspace_modified:
            lines.append("\nChanges not staged for commit:")
            lines.append('  (use "git add/rm <file>..." to update what will be committed)')
            lines.append(
                '  (use "git restore <file>..." to discard changes in working directory)'
            )
            for path in sorted(self.workspace_deleted | self.workspace_modified):
                git_path = GitPath(path, root_dir=self.root_dir)
                lines.append(f"\t\x1b[0;31;40m{self._status_txt(path)}   {git_path}\x1b[0m")

        if self.workspace_added:
            lines.append("\nUntracked files:")
            lines.append('  (use "git add <file>..." to include in what will be committed)')
            for path in sorted(self.workspace_added):
                git_path = GitPath(path, root_dir=self.root_dir)
                lines.append(f"\t\x1b[0;31;40m{git_path}\x1b[0m")
        return ''.join(["\n".join(lines), "\n"])

    def _status_txt(self, file_path: str):
        if file_path in self.workspace_added or file_path in self.index_added:
            return "new file:"
        if file_path in self.workspace_modified or file_path in self.index_modified:
            return "modified:"
        if file_path in self.workspace_deleted or file_path in self.index_deleted:
            return "deleted: "
        raise NotImplementedError

    def _status_code(self, file_path: str):
        codes = [" ", " "]
        if file_path in self.workspace_added and file_path not in self.index_added:
            return "??"
        if file_path in self.workspace_modified:
            codes[1] = "M"
        elif file_path in self.workspace_added:
            codes[1] = "?"
        elif file_path in self.workspace_deleted:
            codes[1] = "D"

        if file_path in self.index_modified:
            codes[0] = "M"
        elif file_path in self.index_added:
            codes[0] = "A"
        elif file_path in self.index_deleted:
            codes[0] = "D"
        return "".join(codes)


class StatusCommand(BaseCommand):
    def __init__(self, root_dir: str, *, porcelain: bool):
        super().__init__(root_dir)
        self.porcelain = porcelain

    def run(self):
        status = FileStatusGroup(root_dir=self.root_dir)

        # check workspace / index differences
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
                    status.workspace_modified.add(str(path))
                continue

            if len(path.parts) == 1:
                status.workspace_added.add(str(path))
            else:
                for parent in reversed(path.parents[:-1]):
                    if str(parent) in status.workspace_added:
                        break
                    if not self.repo.index.has_tracked(parent):
                        status.workspace_added.add(str(parent))
                        break
                else:
                    status.workspace_added.add(str(path))
        for index_file in self.repo.index.entries:
            if index_file not in existed_files:
                status.workspace_deleted.add(index_file)

        # check index / commit differences
        commit: Commit = self.repo.database.load(self.repo.refs.read_head())
        tree: Tree = self.repo.database.load(commit.tree_oid)

        def flatten_tree(
            tree_entries: list[TreeEntry], parent: str = None
        ) -> list[TreeEntry]:
            flatten = []
            for entry in tree_entries:
                entry_path = f"{parent}/{entry.path}" if parent else entry.path
                if GitFileMode(entry.mode).is_file():
                    entry.path = entry_path
                    flatten.append(entry)
                    continue
                sub_tree: Tree = self.repo.database.load(entry.oid)
                flatten.extend(
                    flatten_tree(
                        sub_tree.entries,
                        parent=entry_path,
                    )
                )
            return flatten

        flatten_entries = flatten_tree(tree.entries)
        commit_entries: dict[str, TreeEntry] = {e.path: e for e in flatten_entries}
        for entry_path, index_entry in self.repo.index.entries.items():
            commit_entry = commit_entries.get(entry_path)
            if not commit_entry:
                status.index_added.add(entry_path)
                continue
            if index_entry.to_tree_entry().oid != commit_entry.oid:
                status.index_modified.add(entry_path)
                continue
        for entry_path in commit_entries.keys():
            if entry_path not in self.repo.index.entries:
                status.index_deleted.add(entry_path)

        print(status.porcelain() if self.porcelain else status.long_format())

    def _should_ignore(self, path: Path):
        return any(ignore in path.parts for ignore in self.repo.ignores)
