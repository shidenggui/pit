import hashlib
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class GitObject:
    type: str = field(init=False)
    oid: str = field(init=False)
    saved: bytes = field(init=False)


@dataclass()
class Blob(GitObject):
    content: bytes

    def __post_init__(self):
        self.type = "blob"
        self.saved = b"%s %d\x00%s" % (
            self.type.encode(),
            len(self.content),
            self.content,
        )
        self.oid = hashlib.sha1(self.saved).hexdigest()


@dataclass()
class Commit(GitObject):
    tree_oid: str
    timestamp: int
    timezone: str  # +0800
    user_name: str
    user_email: str
    message: str
    parent_oid: str = None

    def __post_init__(self):
        self.type = "commit"

        # b'commit 188\x00tree 2e81171448eb9f2ee3821e3d447aa6b2fe3ddba1\nauthor shidenggui <longlyshidenggui@gmail.com> 1635305754 +0800\ncommitter shidenggui <longlyshidenggui@gmail.com> 1635305754 +0800\n\nadd a.txt\n'
        user_info = b"%s <%s> %d %s" % (
            self.user_name.encode(),
            self.user_email.encode(),
            self.timestamp,
            self.timezone.encode(),
        )
        contents = [b"tree %s" % self.tree_oid.encode()]
        if self.parent_oid:
            contents.append(b"parent %s" % self.parent_oid.encode())
        contents.append(b"author %s\ncommitter %s" % (user_info, user_info))
        contents.append(b"\n%s\n" % self.message.encode())
        content = b"\n".join(contents)
        self.saved = b"commit %d\x00%s" % (len(content), content)
        self.oid = hashlib.sha1(self.saved).hexdigest()


@dataclass()
class Entry:
    oid: str
    name: str
    mode: bytes = field(default=b"100644")
    saved: bytes = field(init=False)

    def __post_init__(self):
        self.saved = b"%s %s\x00%s" % (
            self.mode,
            self.name.encode(),
            bytes.fromhex(self.oid),
        )


@dataclass()
class Tree(GitObject):
    entries: list[Entry]

    def __post_init__(self):
        self.type = "tree"

        contents = [entry.saved for entry in self.entries]
        content = b"".join(contents)
        self.saved = b"tree %d\x00%s" % (len(content), content)

        self.oid = hashlib.sha1(self.saved).hexdigest()


if __name__ == "__main__":
    print("Test blob")
    a_txt = Blob(content=b"hello\n")
    print(a_txt)
    assert a_txt.saved == b"blob 6\x00hello\n"

    print("Test Tree")
    a_tree = Tree(entries=[Entry(name="a.txt", oid=a_txt.oid)])
    print(a_tree)
    assert (
        a_tree.saved
        == b"tree 33\x00100644 a.txt\x00\xce\x016%\x03\x0b\xa8\xdb\xa9\x06\xf7V\x96\x7f\x9e\x9c\xa3\x94FJ"
    ), a_tree.saved

    print("Test Commit")
    a_commit = Commit(
        tree_oid=a_tree.oid,
        timestamp=1635305754,
        timezone="+0800",
        message="add a.txt",
        user_name="shidenggui",
        user_email="longlyshidenggui@gmail.com",
    )
    print(a_commit)
    assert (
        a_commit.saved
        == b"commit 188\x00tree 2e81171448eb9f2ee3821e3d447aa6b2fe3ddba1\nauthor shidenggui <longlyshidenggui@gmail.com> 1635305754 +0800\ncommitter shidenggui <longlyshidenggui@gmail.com> 1635305754 +0800\n\nadd a.txt\n"
    ), a_tree.saved
