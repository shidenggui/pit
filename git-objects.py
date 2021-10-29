from dataclasses import dataclass
from pathlib import Path
import itertools
import re
import zlib
import sys


@dataclass
class GitObject:
    hash: str
    type: str
    length: int
    content: bytes

    def display(self, mode: str, max_strlen: int = 88):
        display = f"<{self.type.capitalize()}> {self.length} {self.hash}"
        match (mode, self.type):
            case ("full", "blob") if self.length > max_strlen:
                display += f" : {self.content[:max_strlen]}..."
            case ("full", _):
                display += f" : {self.content}"
            case _:
                pass
        return display


def show_git_objects(mode: str, project: str):
    project = Path(project)
    objects_dir = project / ".git/objects"
    objects = list(
        itertools.chain(
            *[[f"{d.name}{f.name}" for f in d.iterdir()] for d in objects_dir.iterdir() if d.name not in {"info", "pack"}]
        )
    )
    git_objects = []
    for obj in objects:
        obj_file = objects_dir / obj[:2] / obj[2:]
        obj_content = zlib.decompress(obj_file.read_bytes())
        type, length, *_ = re.split(b" |\x00", obj_content, maxsplit=2)
        type, length = type.decode(), int(length)
        git_objects.append(
            GitObject(hash=obj, type=type, length=length, content=obj_content)
        )
    git_objects.sort(key=lambda x: {'commit': 1, 'tree': 2, 'blob': 3}[x.type])
    for obj in git_objects:
        print(obj.display(mode=mode))


if __name__ == "__main__":
    show_git_objects(sys.argv[-1], sys.argv[-2])
