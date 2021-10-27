import hashlib
from dataclasses import dataclass, field


@dataclass
class GitObject:
    type: str = field(init=False)
    saved: bytes = field(init=False)
    hash: str = field(init=False)


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
        self.hash = hashlib.sha1(self.saved).hexdigest()


@dataclass()
class Commit(GitObject):
    type: str = "commit"


@dataclass()
class Entry:
    name: str
    hash: str
    mode: bytes = field(default=b"100644")
    saved: bytes = field(init=False)

    def __post_init__(self):
        self.saved = b"%s %s\x00%s" % (
            self.mode,
            self.name.encode(),
            bytes.fromhex(self.hash),
        )


@dataclass()
class Tree(GitObject):
    entries: list[Entry]
    type: str = field(init=False)

    def __post_init__(self):
        self.type = "tree"

        contents = [entry.saved for entry in self.entries]
        content = b"".join(contents)
        self.saved = b"tree %d\x00%s" % (len(content), content)

        self.hash = hashlib.sha1(self.saved).hexdigest()


if __name__ == "__main__":
    print("Test blob")
    a_txt = Blob(content=b"hello\n")
    print(a_txt)
    assert a_txt.saved == b"blob 6\x00hello\n"

    print("Test Tree")
    a_tree = Tree(entries=[Entry(name="a.txt", hash=a_txt.hash)])
    print(a_tree)
    assert (
        a_tree.saved
        == b"tree 33\x00100644 a.txt\x00\xce\x016%\x03\x0b\xa8\xdb\xa9\x06\xf7V\x96\x7f\x9e\x9c\xa3\x94FJ"
    ), a_tree.saved
