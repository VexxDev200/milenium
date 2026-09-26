"""Пути и версия — работают после pip install из любой директории."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

__version__ = "1.6.2"

MILENIUM_HOME = Path.home() / ".milenium"
CONFIG_DIR = MILENIUM_HOME
CONFIG_FILE = CONFIG_DIR / "config.json"
NEON_LOG = MILENIUM_HOME / "milenium.log"

TG_LIBRARY_TARGET = "https://t.me/+pQduDv2K9gE2MTMy"

TG_LIBRARY_SOURCE_LINKS = (
    "https://t.me/+J-d1E0GyCiA3NmRi",
    "https://t.me/+mFFLoewnHoNjZWQy",
    "https://t.me/+3RnTj-8fCSs5OWQ0",
    "https://t.me/+jI4gCRn51Ro0ZTdi",
)

TG_FOLDER_DEFAULT = "бд"

_BUNDLED = Path(__file__).resolve().parent / "bundled"


def _legacy_project_data() -> Path | None:
    """Если запуск из клонированного репо с ./data — сохраняем совместимость."""
    cwd_data = Path.cwd() / "data"
    if not cwd_data.is_dir():
        return None
    markers = (
        cwd_data / "tg_accounts.json",
        cwd_data / "tg_dumps",
        cwd_data / "service_account.json",
    )
    if any(m.exists() for m in markers):
        return cwd_data.resolve()
    return None


def resolve_data_dir() -> Path:
    env = os.environ.get("MILENIUM_DATA_DIR", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    legacy = _legacy_project_data()
    if legacy:
        return legacy
    return (MILENIUM_HOME / "data").resolve()


def _refresh_paths() -> None:
    global DATA_DIR, TG_DUMPS_DIR, TG_ACCOUNTS_FILE, TG_ACCOUNTS_4_FILE
    global TG_FOLDER_SCAN_JSON, TG_SEARCH_JSON

    DATA_DIR = resolve_data_dir()
    TG_DUMPS_DIR = DATA_DIR / "tg_dumps"
    TG_ACCOUNTS_FILE = DATA_DIR / "tg_accounts.json"
    TG_ACCOUNTS_4_FILE = DATA_DIR / "tg_accounts_4.json"
    TG_FOLDER_SCAN_JSON = DATA_DIR / "tg_folder_scan.json"
    TG_SEARCH_JSON = DATA_DIR / "tg_search_results.json"


_refresh_paths()

_layout_done = False


def ensure_layout() -> Path:
    """Создать ~/.milenium/data (или MILENIUM_DATA_DIR) перед первым запуском."""
    global _layout_done
    _refresh_paths()
    MILENIUM_HOME.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TG_DUMPS_DIR.mkdir(parents=True, exist_ok=True)

    example = _BUNDLED / "tg_accounts.example.json"
    readme = _BUNDLED / "DATA_README.txt"

    if not TG_ACCOUNTS_FILE.exists() and example.is_file():
        shutil.copyfile(example, TG_ACCOUNTS_FILE)
    if not TG_ACCOUNTS_4_FILE.exists() and example.is_file():
        shutil.copyfile(example, TG_ACCOUNTS_4_FILE)

    hint = DATA_DIR / "README.txt"
    if not hint.exists() and readme.is_file():
        shutil.copyfile(readme, hint)

    _layout_done = True
    return DATA_DIR


def tool_registry() -> dict:
    from milenium.registry import build_tool_registry

    return build_tool_registry()
