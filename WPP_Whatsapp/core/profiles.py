"""Advisory process lease; never terminate a browser to claim its profile."""

import sys
from pathlib import Path

from .errors import ProfileInUseError


def session_directory(root, name):
    if (
        not isinstance(name, str)
        or not name
        or name in (".", "..")
        or any(c in name for c in "/\\:\x00")
    ):
        raise ValueError("Session name must be a single directory name")
    directory = Path(root).resolve() / name
    directory.mkdir(parents=True, exist_ok=True)
    return str(directory)


class ProfileLease:
    def __init__(self, directory):
        self.path = Path(directory).resolve()
        self.stream = None

    def acquire(self):
        self.path.mkdir(parents=True, exist_ok=True)
        stream = open(self.path / ".wpp-profile.lock", "a+b")
        try:
            stream.seek(0)
            if sys.platform == "win32":
                import msvcrt

                if not stream.read(1):
                    stream.write(b"0")
                    stream.flush()
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            stream.close()
            raise ProfileInUseError("Session profile is already owned by another process") from None
        self.stream = stream
        return self

    def release(self):
        if self.stream is not None:
            # Keep the inode: unlinking a lock file introduces ownership races.
            self.stream.close()
            self.stream = None
