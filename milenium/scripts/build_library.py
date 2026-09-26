#!/usr/bin/env python3
"""
Standalone builder для библиотеки milenium.

После `pip install milenium` доступно как консольная команда:
    milenium-build-library
"""
import argparse
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import milenium


def main():
    parser = argparse.ArgumentParser(description="Собрать лучшие базы и тулки в библиотеку milenium")
    parser.add_argument("--folder", default="бд", help="Название папки TG")
    parser.add_argument("--min-size-mb", type=int, default=50, help="Минимальный размер базы в MB")
    parser.add_argument("--max-files", type=int, default=200, help="Сколько файлов выкачать")
    parser.add_argument("--use-four-accounts", action="store_true", help="Только 4 аккаунта")
    parser.add_argument("--no-upload", action="store_true", help="Только локальная выкачка")
    parser.add_argument("--accounts-file", default=None, help="JSON/CSV с аккаунтами")
    args = parser.parse_args()

    print(f"[build_library] milenium {milenium.__version__}")
    print(f"[build_library] data dir: {milenium.paths()['data']}")
    print(f"[build_library] target: {milenium.TG_LIBRARY_TARGET}")
    print(f"[build_library] старт: folder={args.folder}, min_size={args.min_size_mb}MB, max_files={args.max_files}")

    result = milenium.grab_best(
        folder=args.folder,
        min_size_mb=args.min_size_mb,
        max_files=args.max_files,
        accounts_file=args.accounts_file,
        use_four_accounts=args.use_four_accounts,
        no_upload=args.no_upload,
    )

    print("[build_library] результат:")
    print(result)


if __name__ == "__main__":
    main()
