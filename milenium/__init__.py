import subprocess
import sys
import importlib


def _ensure_deps():
    """Автоустановка зависимостей при первом импорте."""
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
        "PicImageSearch": "PicImageSearch",
    }
    for mod, pkg in deps.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"])
            except Exception:
                pass


_ensure_deps()

__version__ = "1.0.0"