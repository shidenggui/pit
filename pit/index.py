from dataclasses import dataclass
import re
from itertools import chain
from pathlib import Path
import hashlib

from pit.git_object import Blob, TreeEntry
from pit.values import GitFileMode
import os


@dataclass
class IndexHeader:
    """
    - 12 bytes 的头部
        - 4 bytes 固定为 DIRC，为 dircache 的缩写
        - 4 bytes 是 version number，支持2，3，4
        - 4 bytes 为 int32，index entries 的数量
    """

    prefix: str
    version: int
    entries: int

    @classmethod
    def from_raw(cls, raw: bytes) -> "IndexHeader":
        if raw == b"":
            return IndexHeader(
                prefix="DIRC",
                version=int.from_bytes(b"\x00\x00\x00\x02", "big"),
                entries=int.from_bytes(b"\x00\x00\x00\x00", "big"),
            )
        return IndexHeader(
            prefix=raw[:4].decode(),
            version=int.from_bytes(raw[4:8], "big"),
            entries=int.from_bytes(raw[8:12], "big"),
        )

    def __bytes__(self):
        return b"%s%s%s" % (
            self.prefix.encode(),
            self.version.to_bytes(4, "big"),
            self.entries.to_bytes(4, "big"),
        )


@dataclass()
class IndexEntry:
    """
    - 10 个 4 bytes 表示下列值
        - 32-bit ctime seconds, the last time a file's metadata changed
        - 32-bit ctime nansecond fractions
        - 32-bit mtime seconds, the last time a file's data changed
        - 32-bit mtime nanasecond fractions
        - 32-bit dev
        - 32-bit ino
        - 32-bit mode
        - 32-bit uid
        - 32-bit gid
        - 32-bit file size
    - 160-bit (20-byte) SHA-1
    - 16-bit(2-byte) other information，其中包含了文件名的长度
        - 比如 00 08 66 69 6c 65 2e 74 ..file.txt
    - filename
    - 最后 padding zero 使得整个 entry 的长度是 8 的倍数
    - 所有 entries 的最后 60-bit (20-byte) SHA-1 是整个 index 的 hash，防止数据丢失
    """

    ctime: int
    ctime_ns: int
    mtime: int
    mtime_ns: int
    dev: int
    ino: int
    mode: int
    uid: int
    gid: int
    file_size: int
    file_hash: bytes
    file_path_length: int
    file_path: str

    def to_tree_entry(self) -> TreeEntry:
        return TreeEntry(oid=self.file_hash.hex(), path=self.file_path, mode=self.mode)

    def __bytes__(self):
        return b"%s%s%s%s%s%s%s%s%s%s%s%s%s%s" % (
            self.ctime.to_bytes(4, "big"),
            self.ctime_ns.to_bytes(4, "big"),
            self.mtime.to_bytes(4, "big"),
            self.mtime_ns.to_bytes(4, "big"),
            self.dev.to_bytes(4, "big"),
            self.ino.to_bytes(8, "big")[-4:],
            int(bytes(GitFileMode(self.mode)), 8).to_bytes(4, "big"),
            self.uid.to_bytes(4, "big"),
            self.gid.to_bytes(4, "big"),
            self.file_size.to_bytes(4, "big"),
            self.file_hash,
            self.file_path_length.to_bytes(2, "big"),
            self.file_path.encode() + b"\x00",
            b"\x00" * self.padding_zeros,
        )

    @classmethod
    def from_raw(cls, raw: bytes):
        file_path_length = int.from_bytes(raw[60:62], "big")
        return IndexEntry(
            ctime=int.from_bytes(raw[:4], "big"),
            ctime_ns=int.from_bytes(raw[4:8], "big"),
            mtime=int.from_bytes(raw[8:12], "big"),
            mtime_ns=int.from_bytes(raw[12:16], "big"),
            dev=int.from_bytes(raw[16:20], "big"),
            ino=int.from_bytes(raw[20:24], "big"),
            mode=int.from_bytes(raw[24:28], "big"),
            uid=int.from_bytes(raw[28:32], "big"),
            gid=int.from_bytes(raw[32:36], "big"),
            file_size=int.from_bytes(raw[36:40], "big"),
            file_hash=raw[40:60],
            file_path_length=file_path_length,
            file_path=raw[62 : 62 + file_path_length].decode(),
        )

    @classmethod
    def from_file(cls, file: Path) -> ("IndexEntry", Blob):
        """
        os.stat_result(
            st_mode=33261,
            st_ino=12943009244,
            st_dev=16777220,
            st_nlink=1,
            st_uid=501,
            st_gid=20,
            st_size=6,
            st_atime=1635484838,
            st_mtime=1635484837,
            st_ctime=1635484871)
        :param file:
        :return:
        """
        # TODO: when file_path is longer than 4096 bytes,
        # the max value of the file_path_length should be set to 4096 bytes
        # when restoring the overflowed file_path, we should use incremental scanning
        blob = Blob(file.read_bytes())
        file_hash = bytes.fromhex(blob.oid)
        file_stat = file.stat()
        return (
            IndexEntry(
                ctime=int(file_stat.st_ctime),
                ctime_ns=int(file_stat.st_ctime_ns - int(file_stat.st_ctime) * 10 ** 9),
                mtime=int(file_stat.st_mtime),
                mtime_ns=int(file_stat.st_mtime_ns - int(file_stat.st_mtime) * 10 ** 9),
                dev=file_stat.st_dev,
                ino=file_stat.st_ino,
                mode=file_stat.st_mode,
                uid=file_stat.st_uid,
                gid=file_stat.st_gid,
                file_size=file_stat.st_size,
                file_hash=file_hash,
                file_path_length=len(str(file)),
                file_path=str(file),
            ),
            blob,
        )

    @property
    def padding_zeros(self):
        # + 1 because file_path ends with '\x00'
        entry_length = 62 + self.file_path_length + 1
        return 8 - entry_length % 8 if entry_length % 8 else 0

    @property
    def length(self):
        return len(bytes(self))


class Index:
    def __init__(self, root_dir: Path):
        self._root_dir = root_dir
        self._git_dir = self._root_dir / ".git"
        self.index_path = self._git_dir / "index"
        self.header, self.entries = self._parse()

    def __repr__(self):
        return f"<Index(header={self.header}, entries={self.entries})>"

    def __bytes__(self):
        self.header.entries = len(self.entries)
        data = b"%s%s" % (
            self.header,
            b"".join(
                [
                    bytes(e)
                    for e in sorted(self.entries.values(), key=lambda e: e.file_path)
                ]
            ),
        )

        return b"%s%s" % (
            data,
            hashlib.sha1(data).digest(),
        )

    def tracked(self, path: Path) -> bool:
        path = str(Path(path).resolve().relative_to(self._root_dir.resolve()))
        if path in self.entries:
            return True
        if path in self.parents:
            return True
        return False

    @property
    def parents(self):
        parents = set()
        for path in self.entries:
            for p in Path(path).parents:
                parents.add(str(p))
        return parents

    def add_file(self, file_path: Path | str) -> Blob:
        # if sub path try to format the sub path to the path relative to the root dir
        file_path = Path(file_path).resolve().relative_to(self._root_dir.resolve())
        for parent_dir in file_path.parents:
            self.entries.pop(str(parent_dir), None)

        new_entry, blob = IndexEntry.from_file(file_path)
        self.entries[new_entry.file_path] = new_entry
        self.header.entries = len(self.entries)

        return blob

    def clean(self):
        """Clean deleted files"""
        for entry_file_path in list(self.entries):
            if not os.path.exists(entry_file_path):
                self.entries.pop(entry_file_path)
        self.header.entries = len(self.entries)

    def _parse(self):
        raw = self.index_path.read_bytes() if self.index_path.exists() else b""
        header = IndexHeader.from_raw(raw)
        entries = {}
        scanned = 12
        for _ in range(header.entries):
            entry = IndexEntry.from_raw(raw[scanned:])
            entries[entry.file_path] = entry
            scanned += entry.length

        return header, entries


if __name__ == "__main__":
    index = Index("/Users/apple/works/projects/learn/learn_pit/ex2_nested")
    print(index)
    hex_index = (b"%s" % index).hex()
    print(re.findall("\w{4}", hex_index))
