import os
import json
import base64
from pathlib import Path

CONFIG_DIR = Path.home() / ".milenium"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Твои дефолтные значения — вшиты в код.
# Чтобы не палить в открытом виде, они закодированы base64.
# Раскодируй свои и замени строки ниже.
DEFAULT_DATABASE_URL = base64.b64decode(
    "cG9zdGdyZXNxbDovL25lb25kYl9vd25lcjpucGdfSk5Bam5UYXowVUs1QGVwLXR3aWxpZ2h0LWJhci1iMW9mZHlvdC1wb29sZXIuYy01LmV1LWNlbnRyYWwtMS5hd3MubmVvbi50ZWNoL25lb25kYj9zc2xtb2RlPXJlcXVpcmUmY2hhbm5lbF9iaW5kaW5nPXJlcXVpcmU="
).decode()

DEFAULTS = {
    "DATABASE_URL": DEFAULT_DATABASE_URL,
    "SHODAN_API_KEY": "",
    "CENSYS_TOKEN": "",
    "VIRUSTOTAL_API_KEY": "",
    "ABUSEIPDB_KEY": "",
    "IPINFO_TOKEN": "",
    "URLSCAN_API_KEY": "",
    "TG_API_ID": "",
    "TG_API_HASH": "",
    "SERPER_API_KEY": "",
    "HIBP_KEY": "",
    "DEHASHED_EMAIL": "",
    "DEHASHED_KEY": "",
    "LEAKCHECK_KEY": "",
}


def ensure_config():
    """Создаёт конфиг, если его нет. Возвращает словарь."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULTS, indent=2, ensure_ascii=False), encoding="utf-8")
        return dict(DEFAULTS)
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    # Дополняем недостающие ключи
    for k, v in DEFAULTS.items():
        data.setdefault(k, v)
    return data


def get(key, default=""):
    cfg = ensure_config()
    return cfg.get(key, default) or os.environ.get(key, default)


def set_key(key, value):
    cfg = ensure_config()
    cfg[key] = value
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def set_many(pairs: dict):
    cfg = ensure_config()
    cfg.update(pairs)
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def all_keys():
    return ensure_config()


def config_path():
    return str(CONFIG_FILE)


def apply_to_env():
    """Прокидывает конфиг в os.environ, чтобы модули через os.environ.get() его видели."""
    cfg = ensure_config()
    for k, v in cfg.items():
        if v and not os.environ.get(k):
            os.environ[k] = str(v)


def is_first_run():
    return not CONFIG_FILE.exists()