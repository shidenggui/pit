from pathlib import Path


class Refs:
    def __init__(self, root_dir: str | Path):
        self.root_dir = Path(root_dir)
        self.git_dir = self.root_dir / ".git"
        self.refs_dir = self.git_dir / "refs"
        self.head = self.git_dir / "HEAD"

    def init(self):
        self.refs_dir.mkdir(parents=True, exist_ok=True)
        self.head.write_text("ref: refs/heads/main")

    def update_head(self, oid: str):
        self._ref_head().write_text(oid)

    def _ref_head(self):
        ref = self.head.read_text().strip()
        ref_head = self.git_dir / ref[5:]
        if not ref_head.exists():
            ref_head.parent.mkdir(parents=True, exist_ok=True)
        return ref_head

    def read_head(self) -> str | None:
        return self._ref_head().read_text().strip() if self._ref_head().exists() else None


if __name__ == "__main__":
    refs = Refs(Path(__file__).parent.parent)
    print("Current head: ", refs.read_head())
    assert len(refs.read_head()) == 40
    print("Branch main head: ", refs.read_head())
