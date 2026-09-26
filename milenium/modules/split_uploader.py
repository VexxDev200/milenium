import os
import shutil
import subprocess
from pathlib import Path
from milenium.modules import logger


CHUNK_SIZE = 1900 * 1024 * 1024  # 1.9 GB


def _split_with_7z(archive_path, output_dir, chunk_size_mb=1900):
    try:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        base = Path(archive_path).name
        result = subprocess.run(
            [
                "7z", "a", "-v{}m".format(chunk_size_mb),
                str(output_dir / f"{base}.7z"),
                str(archive_path),
            ],
            capture_output=True, text=True, check=True, encoding="utf-8"
        )
        logger.progress(f"SPLIT: нарезан {base}")
        return sorted([str(f) for f in output_dir.iterdir() if f.name.startswith(f"{base}.7z")])
    except FileNotFoundError:
        logger.progress("SPLIT: 7z не найден")
        return []
    except subprocess.CalledProcessError as e:
        logger.progress(f"SPLIT: ошибка {base}: {e.stderr[:200]}")
        return []


def _split_manual(file_path, output_dir, chunk_size=CHUNK_SIZE):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    base = Path(file_path).name
    parts = []
    with open(file_path, "rb") as f:
        idx = 1
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            part_path = output_dir / f"{base}.part{idx:03d}"
            with open(part_path, "wb") as out:
                out.write(chunk)
            parts.append(str(part_path))
            idx += 1
    logger.progress(f"SPLIT: нарезан {base} на {len(parts)} частей")
    return parts


def _split_py7zr(file_path, output_dir, chunk_size_mb=1900):
    try:
        import py7zr
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        base = Path(file_path).name
        archive_out = output_dir / f"{base}.7z"
        with py7zr.SevenZipFile(str(archive_out), "w") as archive:
            archive.write(str(file_path), arcname=Path(file_path).name)
        # После создания архива нарезаем его вручную
        return _split_manual(str(archive_out), output_dir, chunk_size=chunk_size_mb * 1024 * 1024)
    except Exception as e:
        logger.progress(f"SPLIT: py7zr ошибка {Path(file_path).name}: {e}")
        return []


def split_large_file(local_path, output_dir=None):
    local_path = Path(local_path)
    if not output_dir:
        output_dir = local_path.parent / "split_parts"
    else:
        output_dir = Path(output_dir)

    size = local_path.stat().st_size
    if size <= CHUNK_SIZE:
        return [str(local_path)]

    output_dir.mkdir(parents=True, exist_ok=True)

    # Сначала пробуем 7z
    parts = _split_with_7z(local_path, output_dir)
    if parts:
        return parts

    # Fallback: py7zr + manual split
    parts = _split_py7zr(local_path, output_dir)
    if parts:
        return parts

    # Последний fallback: просто части файла
    return _split_manual(local_path, output_dir)


def split_files_in_folder(folder, max_size=CHUNK_SIZE):
    folder = Path(folder)
    all_parts = []
    for f in sorted(folder.iterdir()):
        if not f.is_file():
            continue
        if f.stat().st_size > max_size:
            all_parts.extend(split_large_file(f))
        else:
            all_parts.append(str(f))
    return all_parts
