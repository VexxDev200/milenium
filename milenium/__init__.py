import subprocess
import sys
import importlib

def _ensure_deps():
    deps = {
        "whois": "python-whois",
        "dns": "dnspython",
        "phonenumbers": "phonenumbers",
        "requests": "requests",
        "bs4": "beautifulsoup4",
        "rich": "rich",
        "click": "click",
    }
    for mod, pkg in deps.items():
        try:
            importlib.import_module(mod)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

_ensure_deps()

__version__ = "0.4.0"