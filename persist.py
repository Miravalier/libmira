import shelve
import os
import fcntl
from pathlib import Path


class Persister:
    def __init__(self, path):
        path = Path(path)
        if path.is_absolute():
            self.directory = path
        else:
            self.directory = Path.home() / '.pypersist' / path
        os.makedirs(self.directory, mode=0o755, exist_ok=True)
        self.shelf_path = self.directory / 'shelf'
        self.lock_path = self.directory / 'lock'

    def __enter__(self):
        self.open_lock = _open(str(self.lock_path), 'w')
        fcntl.flock(self.open_lock, fcntl.LOCK_EX)
        self.open_shelf = shelve.open(str(self.shelf_path))
        return self.open_shelf

    def __exit__(self, exception_type, exception_value, traceback):
        self.open_shelf.close()
        fcntl.flock(self.open_lock, fcntl.LOCK_UN)
        self.open_lock.close()

_open = open
def open(path):
    return Persister(path)
