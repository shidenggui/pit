from pathlib import Path
import itertools
import re
import zlib
import sys


def show_git_objects(mode: str, project: str):
    project = Path(project)
    objects_dir = project / ".git/objects"
    objects_prefix_dir = [
        f for f in objects_dir.iterdir() if f.name not in {"info", "pack"}
    ]
    objects = list(
        itertools.chain(
            *[[f"{d.name}{f.name}" for f in d.iterdir()] for d in objects_prefix_dir]
        )
    )
    for obj in objects:
        obj_file = objects_dir / obj[:2] / obj[2:]
        obj_content = zlib.decompress(obj_file.read_bytes())
        typ, length, *_ = re.split(b" |\x00", obj_content, maxsplit=2)
        typ, length = typ.decode(), int(length)

        display = f"{typ} {length} {obj}"
        if mode == "full":
            display += f" : {obj_content}"
        print(display)


if __name__ == "__main__":
    show_git_objects(sys.argv[-2], sys.argv[-1])
