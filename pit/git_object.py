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

    @classmethod
    def from_raw(cls, raw: bytes):
        """
        In [3]: c.split(b'\n')
        Out[3]:
        [b'commit 231\x00tree 798e9d13e6a2b6fcccf20ffb345222462fd4e891',
         b'parent 246c46f09964b12c95aaf73f21a69af0d670e019',
         b'author shidenggui <longlyshidenggui@gmail.com> 1636459276 +0800',
         b'committer shidenggui <longlyshidenggui@gmail.com> 1636459276 +0800',
         b'',
         b'init',
         b'']
        :param raw:
        :return:
        """
        lines = raw.split(b"\n")
        _, tree_info = lines[0].split(b"\x00")
        tree_oid = tree_info[5:].decode()
        parent_oid = lines[1][7:].decode() if lines[1].startswith(b"parent") else None

        line_no = 2 if parent_oid else 1
        _, author_name, author_email, timestamp, timezone = lines[line_no].split(b" ")

        # remove <> around '<longlyshidenggui@gmail.com>'
        author_email = author_email[1:-1]
        line_no += 3
        commit_msg = b"\n".join(lines[line_no:-1]).decode()
        return Commit(
            tree_oid=tree_oid,
            author=AuthorSign(
                name=author_name.decode(),
                email=author_email.decode(),
                timestamp=int(timestamp),
                timezone=timezone.decode(),
            ),
            message=commit_msg,
            parent_oid=parent_oid,
        )


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
    a_tree = Tree(
        entries=[TreeEntry(path="a.txt", oid=a_txt.oid, mode=int(b"100644", 8))]
    )
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
    expected_commit = b"commit 188\x00tree 2e81171448eb9f2ee3821e3d447aa6b2fe3ddba1\nauthor shidenggui <longlyshidenggui@gmail.com> 1635305754 +0800\ncommitter shidenggui <longlyshidenggui@gmail.com> 1635305754 +0800\n\nadd a.txt\n"
    assert bytes(a_commit) == expected_commit, bytes(a_tree)
    assert Commit.from_raw(expected_commit) == a_commit, Commit.from_raw(
        expected_commit
    )

    # with parent
    expected_commit = b"commit 231\x00tree 798e9d13e6a2b6fcccf20ffb345222462fd4e891\nparent 246c46f09964b12c95aaf73f21a69af0d670e019\nauthor shidenggui <longlyshidenggui@gmail.com> 1636459276 +0800\ncommitter shidenggui <longlyshidenggui@gmail.com> 1636459276 +0800\n\ninit\n"
    assert Commit.from_raw(expected_commit) == Commit(
        tree_oid="798e9d13e6a2b6fcccf20ffb345222462fd4e891",
        author=AuthorSign(
            name="shidenggui",
            email="longlyshidenggui@gmail.com",
            timestamp=1636459276,
            timezone="+0800",
        ),
        message="init",
        parent_oid="246c46f09964b12c95aaf73f21a69af0d670e019",
    ), Commit.from_raw(expected_commit)
