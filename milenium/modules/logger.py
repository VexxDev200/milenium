# milenium/modules/logger.py
import sys
import os
from datetime import datetime

class TeeLogger:
    """
    Пишет в консоль и в файл одновременно.
    Использование:
        import sys
        from milenium.modules.logger import TeeLogger
        sys.stdout = TeeLogger("milenium.log")
    """
    def __init__(self, filepath, mode="a"):
        self.terminal = sys.__stdout__
        self.file = open(filepath, mode, encoding="utf-8", buffering=1)  # line buffered
        self._write_header()

    def _write_header(self):
        ts = datetime.now().isoformat()
        self.file.write(f"\n{'='*60}\n[SESSION START] {ts}\n{'='*60}\n")
        self.file.flush()

    def write(self, message):
        self.terminal.write(message)
        self.file.write(message)
        self.file.flush()  # сразу на диск, без буферизации

    def flush(self):
        self.terminal.flush()
        self.file.flush()

    def close(self):
        self.file.close()
        sys.stdout = self.terminal