from pathlib import Path

from pit.exceptions import BranchAlreadyExists
from pit.values import BranchName


class Refs:
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.git_dir = self.root_dir / ".git"
        self.refs_dir = self.git_dir / "refs/heads"
        self.head = self.git_dir / "HEAD"

    def init(self):
        self.refs_dir.mkdir(parents=True, exist_ok=True)
        self.head.write_text("ref: refs/heads/main")

    def update_ref_head(self, oid: str):
        self._ref_head().write_text(oid)

    def update_head(self, *, oid: str = None, branch: str = None):
        assert oid or branch, "Must provide one of the oid or branch args"
        if oid:
            self.head.write_text(oid)
        else:
            self.head.write_text(f"ref: refs/heads/{branch}")

    def create_branch(self, name: str, oid: str):
        branch_name = BranchName(name)
        branch_path = self.refs_dir / str(branch_name)
        if branch_path.exists():
            raise BranchAlreadyExists(str(branch_name))
        branch_path.write_text(oid)

    def list_branches(self) -> list[str]:
        return [branch.name for branch in self.refs_dir.iterdir()]

    def read_branch(self, name: str) -> str:
        branch_name = BranchName(name)
        branch_path = self.refs_dir / str(branch_name)
        return branch_path.read_text().strip()

    def _write_branch(self, path: Path, oid: str):
        path.write_text(oid)

    def read_head(self) -> str | None:
        if not self.head.exists():
            return None
        head = self.head.read_text().strip()
        if head.startswith("ref: "):
            return self._ref_head().read_text().strip()
        return head

    def _ref_head(self) -> Path:
        ref = self.head.read_text().strip()
        ref_head = self.git_dir / ref[5:]
        if not ref_head.exists():
            ref_head.parent.mkdir(parents=True, exist_ok=True)
        return ref_head


if __name__ == "__main__":
    refs = Refs(Path(__file__).parent.parent)
    print("Current head: ", refs.read_head())
    assert len(refs.read_head()) == 40
    print("Branch main head: ", refs.read_head())
