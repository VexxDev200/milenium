"""
Полный каталог модулей, CLI и баз данных пакета milenium.
Источник правды для library.tools(), list_modules(), list_databases().
"""
from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

from milenium.constants import DATA_DIR, TG_DUMPS_DIR

# category → { module_name: {entry, desc, cli?} }
MODULE_CATALOG: dict[str, dict[str, dict[str, str]]] = {
    "osint_search": {
        "aggregator": {"entry": "run", "desc": "Сборка OSINT (email/user/ip/url/phone)"},
        "maigret_search": {"entry": "check", "desc": "Maigret — ники по сайтам"},
        "sherlock_search": {"entry": "check", "desc": "Sherlock — ники"},
        "holehe_search": {"entry": "check", "desc": "Holehe — регистрации по email"},
        "leak_search": {"entry": "niamonx_search, hibp_test", "desc": "NiamonX + HIBP"},
        "hibp": {"entry": "check_email", "desc": "Have I Been Pwned"},
        "leakcheck": {"entry": "search", "desc": "LeakCheck API"},
        "dehashed": {"entry": "search", "desc": "DeHashed"},
        "pwned_passwords": {"entry": "check_password", "desc": "Pwned Passwords (k-anonymity)"},
        "breach": {"entry": "check", "desc": "Агрегатор утечек (legacy)"},
        "breach_local": {"entry": "search", "desc": "Локальный BreachCompilation (папка)"},
        "username": {"entry": "check", "desc": "Проверка ника + пермутации"},
        "permutator": {"entry": "generate", "desc": "Генерация вариантов ника"},
        "email": {"entry": "check", "desc": "Email OSINT (legacy)"},
        "email_validator": {"entry": "check", "desc": "Валидация email"},
        "phone": {"entry": "check", "desc": "Phone (legacy)"},
        "ip": {"entry": "check", "desc": "IP (legacy)"},
        "domain": {"entry": "check", "desc": "WHOIS / domain"},
        "social": {"entry": "check", "desc": "Social profiles (legacy)"},
        "dorker": {"entry": "search_nick", "desc": "Google dorks (Serper)"},
        "report": {"entry": "build", "desc": "Сбор отчёта"},
    },
    "osint_network": {
        "shodan_search": {"entry": "check_ip", "desc": "Shodan API"},
        "shodan_lite": {"entry": "check_ip", "desc": "Shodan без ключа (ограничено)"},
        "censys_search": {"entry": "check_host", "desc": "Censys host"},
        "virustotal_search": {"entry": "check_ip", "desc": "VirusTotal IP/URL"},
        "abuseipdb_search": {"entry": "check", "desc": "AbuseIPDB"},
        "ipinfo_search": {"entry": "check", "desc": "ipinfo.io"},
        "urlscan_search": {"entry": "check", "desc": "urlscan.io"},
        "ip_reputation": {"entry": "check", "desc": "IP reputation composite"},
        "ip_geo_advanced": {"entry": "check", "desc": "Расширенная геолокация IP"},
        "dns_history": {"entry": "check", "desc": "История DNS"},
        "reverse_whois": {"entry": "check", "desc": "Reverse WHOIS"},
        "wayback": {"entry": "check", "desc": "Wayback Machine"},
        "wifi_geolocation": {"entry": "check", "desc": "WiFi BSSID → geo"},
    },
    "osint_social": {
        "telegram_osint": {"entry": "check_channel", "desc": "TG канал (HTTP)"},
        "telegram_analysis": {"entry": "check_user", "desc": "Telethon профиль"},
        "tg_parser": {"entry": "parse", "desc": "Парсер TG сообщений"},
        "vk_osint": {"entry": "check", "desc": "VK"},
        "twitter_osint": {"entry": "check", "desc": "Twitter/X"},
        "instagram_osint": {"entry": "check", "desc": "Instagram"},
        "github_search": {"entry": "check_email, check_username", "desc": "GitHub"},
        "gravatar": {"entry": "check", "desc": "Gravatar по email"},
        "pgp_lookup": {"entry": "check", "desc": "PGP ключи"},
    },
    "osint_media": {
        "image_search": {"entry": "search", "desc": "Обратный поиск по фото"},
        "exif_extractor": {"entry": "check", "desc": "EXIF из изображения"},
    },
    "osint_ru": {
        "dadata_search": {"entry": "search_company, search_phone", "desc": "DaData компании/телефон"},
        "fssp_search": {"entry": "check_physical", "desc": "ФССП долги"},
    },
    "database": {
        "neon_db": {"entry": "init, save, stats, query", "desc": "Neon Postgres — история OSINT"},
        "csv_db": {"entry": "init_db, search, exact, stats", "desc": "CSV → SQLite FTS5"},
    },
    "telegram": {
        "tg_scraper": {"entry": "run", "desc": "Grab каналов/папки + upload"},
        "tg_folder_scanner": {"entry": "run", "desc": "Скан папки TG на базы"},
        "tg_searcher": {"entry": "run", "desc": "Поиск каналов с базами"},
        "tg_reupload": {"entry": "run_reupload", "desc": "Локаль → TG"},
        "tg_bot": {"entry": "main", "desc": "Aiogram бот"},
        "virus_check": {"entry": "check_file_vt", "desc": "VirusTotal файлов"},
        "gdrive_uploader": {"entry": "upload", "desc": "Google Drive upload"},
        "split_uploader": {"entry": "split_and_upload", "desc": "Сплит больших файлов"},
    },
    "system": {
        "config": {"entry": "get, set_key, all_keys", "desc": "~/.milenium/config.json + LOCKED keys"},
        "logger": {"entry": "progress, TeeLogger", "desc": "Лог и прогресс CLI/TUI"},
    },
}

CLI_CATALOG: dict[str, dict[str, str]] = {
    "user": {"module": "aggregator", "desc": "Maigret + Sherlock", "group": "osint"},
    "email_cmd": {"module": "aggregator", "desc": "Holehe + leaks", "group": "osint"},
    "ip_cmd": {"module": "aggregator", "desc": "Shodan, Censys, VT, AbuseIPDB, ipinfo", "group": "osint"},
    "url_cmd": {"module": "aggregator", "desc": "urlscan.io", "group": "osint"},
    "leak": {"module": "leak_search", "desc": "NiamonX + HIBP", "group": "osint"},
    "company": {"module": "dadata_search", "desc": "DaData компания", "group": "osint_ru"},
    "phone_info": {"module": "dadata_search", "desc": "DaData телефон", "group": "osint_ru"},
    "fssp": {"module": "fssp_search", "desc": "ФССП", "group": "osint_ru"},
    "tg": {"module": "telegram_analysis", "desc": "Telethon профиль", "group": "telegram"},
    "img": {"module": "image_search", "desc": "PicImageSearch", "group": "osint_media"},
    "db_neon": {"module": "neon_db", "desc": "Neon статистика/поиск", "group": "database"},
    "config_cmd": {"module": "config", "desc": "API ключи", "group": "system"},
    "csv import": {"module": "csv_db", "desc": "Импорт CSV", "group": "database"},
    "csv search": {"module": "csv_db", "desc": "FTS/LIKE", "group": "database"},
    "csv exact": {"module": "csv_db", "desc": "Точное поле", "group": "database"},
    "csv stats": {"module": "csv_db", "desc": "Статистика SQLite", "group": "database"},
    "tg_grab": {"module": "tg_scraper", "desc": "Скачать из TG", "group": "telegram"},
    "tg_library": {"module": "library", "desc": "Alias sync_library", "group": "telegram"},
    "library sync": {"module": "library", "desc": "Invite + папка → архив", "group": "telegram"},
    "library grab-best": {"module": "library", "desc": "Лучшие базы + тулки → архив", "group": "telegram"},
    "library build": {"module": "library", "desc": "Standalone builder → архив", "group": "telegram"},
    "library build-full": {"module": "library", "desc": "Полная сборка библиотеки", "group": "telegram"},
    "library tools": {"module": "registry", "desc": "Каталог", "group": "system"},
    "library paths": {"module": "library", "desc": "Пути data/", "group": "system"},
    "library modules": {"module": "registry", "desc": "Все Python-модули", "group": "system"},
    "library databases": {"module": "registry", "desc": "Neon + локальные файлы", "group": "database"},
    "tg_scan_folder": {"module": "tg_folder_scanner", "desc": "Скан папки TG", "group": "telegram"},
    "tg_search": {"module": "tg_searcher", "desc": "Поиск каналов", "group": "telegram"},
    "tg_reupload": {"module": "tg_reupload", "desc": "Reupload в архив", "group": "telegram"},
    "bot": {"module": "tg_bot", "desc": "Telegram bot", "group": "telegram"},
    "tui": {"module": "tui", "desc": "Интерактивный UI", "group": "system"},
}

DATABASE_KINDS = {
    "neon": {
        "type": "postgresql",
        "module": "neon_db",
        "desc": "Облачная история запросов (results, findings, leaks)",
        "config_key": "DATABASE_URL",
    },
    "csv_sqlite": {
        "type": "sqlite",
        "module": "csv_db",
        "desc": "Рядом с CSV: *.milenium.sqlite",
        "pattern": "*.milenium.sqlite",
    },
    "tg_dumps": {
        "type": "files",
        "path_key": "tg_dumps",
        "desc": "Выкачанные базы из Telegram",
        "extensions": (
            ".sql", ".sqlite", ".db", ".csv", ".txt",
            ".gz", ".zip", ".7z", ".rar", ".xlsx",
        ),
    },
    "breach_local": {
        "type": "directory_tree",
        "module": "breach_local",
        "desc": "Распакованный BreachCompilation — milenium.breach_local.search(q, path)",
        "env": "BREACH_LOCAL_PATH",
    },
    "tg_scan_report": {
        "type": "json",
        "path_key": "tg_folder_scan",
        "desc": "Отчёт tg_scan_folder",
    },
    "tg_search_report": {
        "type": "json",
        "path_key": "tg_search",
        "desc": "Результаты tg_search",
    },
}

LOCAL_DB_EXTENSIONS = frozenset(
    {
        ".sqlite", ".db", ".sql", ".csv", ".milenium.sqlite",
        ".json", ".txt", ".gz", ".zip", ".7z", ".rar", ".xlsx",
    }
)


def module_count() -> int:
    return sum(len(v) for v in MODULE_CATALOG.values())


def cli_count() -> int:
    return len(CLI_CATALOG)


def build_tool_registry() -> dict[str, dict[str, str]]:
    """Сводка для milenium tools() — по группам CLI."""
    groups: dict[str, dict[str, str]] = {
        "osint": {},
        "database": {},
        "telegram": {},
        "system": {},
    }
    for cmd, meta in CLI_CATALOG.items():
        g = meta.get("group", "system")
        if g not in groups:
            groups[g] = {}
        groups[g][cmd] = meta["desc"]
    return groups


def list_modules(flat=False) -> dict[str, Any] | list[dict[str, str]]:
    if flat:
        out = []
        for cat, mods in MODULE_CATALOG.items():
            for name, meta in mods.items():
                out.append(
                    {
                        "category": cat,
                        "name": name,
                        "import": f"milenium.modules.{name}",
                        "entry": meta["entry"],
                        "desc": meta["desc"],
                    }
                )
        return out
    return MODULE_CATALOG


def load_module(name: str):
    """import milenium.modules.<name>"""
    if name.startswith("milenium."):
        return importlib.import_module(name)
    return importlib.import_module(f"milenium.modules.{name}")


def scan_local_database_files(
    root: Path | None = None,
    *,
    max_files: int = 8000,
    max_depth: int = 6,
) -> list[dict[str, Any]]:
    """Файлы баз в data/ (рекурсивно)."""
    root = (root or DATA_DIR).resolve()
    if not root.exists():
        return []
    found: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if len(found) >= max_files:
            break
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if path.is_dir():
            continue
        if len(rel.parts) > max_depth:
            continue
        suf = path.suffix.lower()
        if path.name.endswith(".milenium.sqlite"):
            kind = "csv_sqlite"
        elif suf in LOCAL_DB_EXTENSIONS:
            kind = "file"
        else:
            continue
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        found.append(
            {
                "path": str(path),
                "relative": str(rel).replace("\\", "/"),
                "kind": kind,
                "ext": suf or path.suffix,
                "size_bytes": size,
            }
        )
    found.sort(key=lambda x: (-x["size_bytes"], x["relative"]))
    return found


def list_databases(include_scan: bool = True) -> dict[str, Any]:
    from milenium.constants import TG_FOLDER_SCAN_JSON, TG_SEARCH_JSON

    path_map = {
        "tg_dumps": str(TG_DUMPS_DIR),
        "tg_folder_scan": str(TG_FOLDER_SCAN_JSON),
        "tg_search": str(TG_SEARCH_JSON),
        "data": str(DATA_DIR),
    }
    out: dict[str, Any] = {
        "kinds": DATABASE_KINDS,
        "paths": path_map,
        "modules": ["neon_db", "csv_db", "breach_local"],
    }
    if include_scan:
        out["local_files"] = scan_local_database_files()
        out["local_files_count"] = len(out["local_files"])
    return out
