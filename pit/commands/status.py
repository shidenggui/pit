from pit.commands.base import BaseCommand
from pit.constants import Color
from pit.repository import FileStatusGroup
from pit.values import GitPath


class StatusCommand(BaseCommand):
    def __init__(self, root_dir: str, *, porcelain: bool):
        super().__init__(root_dir)
        self.porcelain = porcelain

    def run(self):
        print(
            self._display_porcelain(self.repo.status)
            if self.porcelain
            else self._display_long_format(self.repo.status)
        )

    def _display_porcelain(self, status: FileStatusGroup) -> str:
        lines = []
        for path in (
            status.workspace_added
            | status.workspace_modified
            | status.workspace_deleted
            | status.index_deleted
            | status.index_modified
            | status.index_added
        ):
            git_path = GitPath(path, root_dir=status.root_dir)
            lines.append(f"{self._status_code(path, status)} {git_path}")
        lines.sort(key=lambda x: "zz" if x[:2] == "??" else x[3:])
        return "\n".join(lines)

    def _display_long_format(self, status: FileStatusGroup) -> str:
        lines = []
        if status.index_added or status.index_modified or status.index_deleted:
            lines.append("Changes to be committed:")
            lines.append('  (use "git restore --staged <file>..." to unstage)')
            for path in sorted(
                status.index_deleted | status.index_modified | status.index_added
            ):
                git_path = GitPath(path, root_dir=status.root_dir)
                lines.append(
                    f"\t\x1b[7;30;42m{self._status_txt(path, status)}   {git_path}\x1b[0m"
                )

        if status.workspace_deleted or status.workspace_modified:
            lines.append("\nChanges not staged for commit:")
            lines.append(
                '  (use "git add/rm <file>..." to update what will be committed)'
            )
            lines.append(
                '  (use "git restore <file>..." to discard changes in working directory)'
            )
            for path in sorted(status.workspace_deleted | status.workspace_modified):
                git_path = GitPath(path, root_dir=status.root_dir)
                lines.append(
                    f"\t{Color.RED}{self._status_txt(path, status)}   {git_path}{Color.RESET_ALL}"
                )

        if status.workspace_added:
            lines.append("\nUntracked files:")
            lines.append(
                '  (use "git add <file>..." to include in what will be committed)'
            )
            for path in sorted(status.workspace_added):
                git_path = GitPath(path, root_dir=status.root_dir)
                lines.append(f"\t{Color.RED}{git_path}{Color.RESET_ALL}")
        return "".join(["\n".join(lines), "\n"])

    def _status_txt(self, file_path: str, status: FileStatusGroup) -> str:
        if file_path in status.workspace_added or file_path in status.index_added:
            return "new file:"
        if file_path in status.workspace_modified or file_path in status.index_modified:
            return "modified:"
        if file_path in status.workspace_deleted or file_path in status.index_deleted:
            return "deleted: "
        raise NotImplementedError

    def _status_code(self, file_path: str, status: FileStatusGroup) -> str:
        codes = [" ", " "]
        if file_path in status.workspace_added and file_path not in status.index_added:
            return "??"
        if file_path in status.workspace_modified:
            codes[1] = "M"
        elif file_path in status.workspace_added:
            codes[1] = "?"
        elif file_path in status.workspace_deleted:
            codes[1] = "D"

        if file_path in status.index_modified:
            codes[0] = "M"
        elif file_path in status.index_added:
            codes[0] = "A"
        elif file_path in status.index_deleted:
            codes[0] = "D"
        return "".join(codes)
