#!/usr/bin/env python3
"""
Полная standalone сборка библиотеки milenium.

Команда после pip install:
    milenium-build-library-full
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
    parser = argparse.ArgumentParser(description="Полная сборка библиотеки milenium")
    parser.add_argument("--folder", default="бд")
    parser.add_argument("--min-size-mb", type=int, default=50)
    parser.add_argument("--max-files", type=int, default=500)
    parser.add_argument("--use-four-accounts", action="store_true")
    parser.add_argument("--no-upload", action="store_true")
    args = parser.parse_args()

    print(f"[build_library_full] milenium {milenium.__version__}")
    print(f"[build_library_full] data dir: {milenium.paths()['data']}")

    print("[build_library_full] 1/3 скан папки «бд»...")
    scan = milenium.scan_tg_folder(args.folder)
    print(f"[build_library_full] strong={scan.get('strong', 0)}, yes={scan.get('yes', 0)}")

    print("[build_library_full] 2/3 поиск публичных каналов с базами...")
    search = milenium.search_tg_channels()
    print(f"[build_library_full] найдено каналов: {search.get('count', 0)}")

    print("[build_library_full] 3/3 выкачка лучшего...")
    result = milenium.grab_best(
        folder=args.folder,
        min_size_mb=args.min_size_mb,
        max_files=args.max_files,
        use_four_accounts=args.use_four_accounts,
        no_upload=args.no_upload,
    )
    print("[build_library_full] результат:")
    print(result)


if __name__ == "__main__":
    main()
