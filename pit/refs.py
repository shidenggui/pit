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

    def is_detached(self) -> bool:
        return not self.head.read_text().startswith("ref: ")

    def update_ref_head(self, oid: str):
        ref_path = self._find_ref(self.head)
        ref_path.write_text(oid)

    def update_head(self, *, oid: str = None, branch: str = None):
        assert oid or branch, "Must provide one of the oid or branch args"
        if oid:
            self.head.write_text(oid)
        else:
            self.head.write_text(f"ref: refs/heads/{branch}")

    def read_head(self) -> str | None:
        if not self.head.exists():
            return None
        return self._find_ref(self.head).read_text().strip() or None

    def read_ref(self, name: str) -> str | None:
        ref_path = self.refs_dir / name
        if not ref_path.exists():
            return None
        return self._find_ref(ref_path).read_text().strip() or None

    def _find_ref(self, ref_path: Path) -> Path:
        if not ref_path.exists():
            ref_path.parent.mkdir(parents=True, exist_ok=True)
            ref_path.write_text("")
            return ref_path

        ref = ref_path.read_text().strip()
        if not ref.startswith("ref: "):
            return ref_path
        child = self.git_dir / ref[5:]
        return self._find_ref(child)

    def create_branch(self, name: str, oid: str):
        branch_name = BranchName(name)
        branch_path = self.refs_dir / str(branch_name)
        if branch_path.exists():
            raise BranchAlreadyExists(str(branch_name))
        branch_path.write_text(oid)

    def list_branches(self) -> list[str]:
        return [branch.name for branch in self.refs_dir.iterdir()]

    def delete_branch(self, name: str):
        branch_path = self.refs_dir / str(name)
        branch_path.unlink(missing_ok=True)

    def read_branch(self, name: str) -> str:
        branch_name = BranchName(name)
        branch_path = self.refs_dir / str(branch_name)
        return self._find_ref(branch_path).read_text().strip()

    def current_branch(self) -> str | None:
        if self.is_detached():
            return None
        return self.head.read_text().split("/")[-1]

    def _write_branch(self, path: Path, oid: str):
        path.write_text(oid)


if __name__ == "__main__":
    refs = Refs(Path(__file__).parent.parent)
    print("Current head: ", refs.read_head())
    assert len(refs.read_head()) == 40
    print("Branch main head: ", refs.read_head())
