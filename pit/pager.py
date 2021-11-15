import subprocess
import sys
from contextlib import contextmanager


@contextmanager
def pager():
    try:
        "-F for quit-if-one-screen"
        "To prevent less from clearing the screen upon exit, use -X"
        pager = subprocess.Popen(
            ["less", "-c", "-R", "-S", "-K"],
            stdin=subprocess.PIPE,
            stdout=sys.stdout,
            text=True,
        )
        sys.stdout = pager.stdin

        yield

        pager.stdin.close()
        pager.wait()
    except KeyboardInterrupt:
        pass
