import sys
import os
from datetime import datetime

PROGRESS_CALLBACK = None


def set_progress_callback(cb):
    global PROGRESS_CALLBACK
    PROGRESS_CALLBACK = cb


def progress(text):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {text}"
    if PROGRESS_CALLBACK:
        PROGRESS_CALLBACK(line)
    if sys.__stdout__:
        try:
            sys.__stdout__.write(line + "\n")
            sys.__stdout__.flush()
        except Exception:
            pass


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
        if self.terminal:
            try:
                self.terminal.write(message)
            except Exception:
                pass
        self.file.write(message)
        self.file.flush()

    def flush(self):
        if self.terminal:
            try:
                self.terminal.flush()
            except Exception:
                pass
        self.file.flush()

    def close(self):
        self.file.close()
        sys.stdout = self.terminal

    @property
    def path(self):
        return self.filepath