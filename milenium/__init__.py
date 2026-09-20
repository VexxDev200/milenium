import subprocess
import sys
import importlib


def _ensure_deps():
    deps = {
        "requests": "requests",
        "aiohttp": "aiohttp",
        "dns": "dnspython",
        "phonenumbers": "phonenumbers",
        "bs4": "beautifulsoup4",
        "rich": "rich",
        "click": "click",
        "whois": "python-whois",
        "psycopg2": "psycopg2-binary",
        "telethon": "telethon",
        "aiogram": "aiogram",
    }
    for mod, pkg in deps.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", pkg, "--quiet"]
                )
            except Exception:
                pass


_ensure_deps()

__version__ = "1.2.1"