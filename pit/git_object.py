import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from pit.values import GitFileMode, AuthorSign


@dataclass
class GitObject:
    type: str = field(init=False)
    oid: str = field(init=False)


@dataclass()
class Blob(GitObject):
    content: bytes

    def __post_init__(self):
        self.type = "blob"
        self.oid = hashlib.sha1(bytes(self)).hexdigest()

    def __bytes__(self):
        return b"%s %d\x00%s" % (
            self.type.encode(),
            len(self.content),
            self.content,
        )


@dataclass()
class Commit(GitObject):
    tree_oid: str
    author: AuthorSign
    message: str
    parent_oid: str = None

    def __post_init__(self):
        self.type = "commit"
        self.oid = hashlib.sha1(bytes(self)).hexdigest()

    def __bytes__(self):
        # b'commit 188\x00tree 2e81171448eb9f2ee3821e3d447aa6b2fe3ddba1\nauthor shidenggui <longlyshidenggui@gmail.com> 1635305754 +0800\ncommitter shidenggui <longlyshidenggui@gmail.com> 1635305754 +0800\n\nadd a.txt\n'
        contents = [b"tree %s" % self.tree_oid.encode()]
        if self.parent_oid:
            contents.append(b"parent %s" % self.parent_oid.encode())
        contents.append(b"author %s\ncommitter %s" % (self.author, self.author))
        contents.append(b"\n%s\n" % self.message.encode())
        content = b"\n".join(contents)
        return b"commit %d\x00%s" % (len(content), content)


@dataclass()
class TreeEntry:
    oid: str
    path: str
    mode: int

    def __bytes__(self):
        return b"%s %s\x00%s" % (
            GitFileMode(self.mode),
            Path(self.path).name.encode(),
            bytes.fromhex(self.oid),
        )


@dataclass()
class Tree(GitObject):
    entries: list["TreeEntry"]

    def __post_init__(self):
        self.type = "tree"
        self.entries = sorted(self.entries, key=lambda x: Path(x.path).name)

    @property
    def oid(self):
        return hashlib.sha1(bytes(self)).hexdigest()

    def __bytes__(self):
        contents = [bytes(entry) for entry in self.entries]
        content = b"".join(contents)
        return b"tree %d\x00%s" % (len(content), content)


if __name__ == "__main__":
    print("Test blob")
    a_txt = Blob(content=b"hello\n")
    print(a_txt)
    assert bytes(a_txt) == b"blob 6\x00hello\n"

    print("Test Tree")
    a_tree = Tree(entries=[TreeEntry(path="a.txt", oid=a_txt.oid, mode=int(b'100644', 8))])
    print(a_tree)
    assert (
        bytes(a_tree)
        == b"tree 33\x00100644 a.txt\x00\xce\x016%\x03\x0b\xa8\xdb\xa9\x06\xf7V\x96\x7f\x9e\x9c\xa3\x94FJ"
    ), bytes(a_tree)

    print("Test Commit")
    a_commit = Commit(
        tree_oid=a_tree.oid,
        author=AuthorSign(
            name="shidenggui",
            email="longlyshidenggui@gmail.com",
            timestamp=1635305754,
            timezone="+0800",
        ),
        message="add a.txt",
    )
    print(a_commit)
    assert (
        bytes(a_commit)
        == b"commit 188\x00tree 2e81171448eb9f2ee3821e3d447aa6b2fe3ddba1\nauthor shidenggui <longlyshidenggui@gmail.com> 1635305754 +0800\ncommitter shidenggui <longlyshidenggui@gmail.com> 1635305754 +0800\n\nadd a.txt\n"
    ), bytes(a_tree)
