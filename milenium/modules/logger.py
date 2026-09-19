import sys
import os
from datetime import datetime

class TeeLogger:
    def __init__(self, filepath="milenium.log", mode="a"):
        self.filepath = os.path.abspath(filepath)
        self.terminal = sys.__stdout__
        self.file = open(self.filepath, mode, encoding="utf-8", buffering=1)
        self._write_header()

    def _write_header(self):
        ts = datetime.now().isoformat()
        self.file.write(f"\n{'='*60}\n[SESSION START] {ts}\n{'='*60}\n")
        self.file.flush()

    def write(self, message):
        self.terminal.write(message)
        self.file.write(message)
        self.file.flush()

    def flush(self):
        self.terminal.flush()
        self.file.flush()

    def close(self):
        self.file.close()
        sys.stdout = self.terminal

    @property
    def path(self):
        return self.filepath