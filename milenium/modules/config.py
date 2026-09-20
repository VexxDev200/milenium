import os
import json
import base64
from pathlib import Path

CONFIG_DIR = Path.home() / ".milenium"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _b64(s: str) -> str:
    return base64.b64decode(s).decode()


# ═══════════════════════════════════════════════════
# LOCKED — вшито в код, менять нельзя
# ═══════════════════════════════════════════════════
# ВАЖНО: замени base64 на свой НОВЫЙ токен и свой ID.
# Закодировать: python -c "import base64; print(base64.b64encode(b'...').decode())"

LOCKED = {
    "DATABASE_URL": _b64(
        "cG9zdGdyZXNxbDovL25lb25kYl9vd25lcjpucGdfSk5Bam5UYXowVUs1QGVwLXR3aWxpZ2h0LWJhci1iMW9mZHlvdC1wb29sZXIuYy01LmV1LWNlbnRyYWwtMS5hd3MubmVvbi50ZWNoL25lb25kYj9zc2xtb2RlPXJlcXVpcmUmY2hhbm5lbF9iaW5kaW5nPXJlcXVpcmU="
    ),
    "TG_API_ID": "28088599",
    "TG_API_HASH": "8df5e438f9b66dba136e70a1e7a2edb4",
    "TG_BOT_TOKEN": _b64("ODgxMjMyMTIyNTpBQUZndEpvX2laLVFhYnFEZzJnbWdDWU1ERDJHUlhFYl9yWQ=="),
    "TG_ALLOWED_USERS": "5496853233",
}


DEFAULTS = {
    "SHODAN_API_KEY": "",
    "CENSYS_TOKEN": "",
    "VIRUSTOTAL_API_KEY": "",
    "ABUSEIPDB_KEY": "",
    "IPINFO_TOKEN": "",
    "URLSCAN_API_KEY": "",
    "SERPER_API_KEY": "",
    "HIBP_KEY": "",
    "DEHASHED_EMAIL": "",
    "DEHASHED_KEY": "",
    "LEAKCHECK_KEY": "",
}


def ensure_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        data = {k: v for k, v in DEFAULTS.items() if k not in LOCKED}
        CONFIG_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return data
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    for k, v in DEFAULTS.items():
        if k not in LOCKED:
            data.setdefault(k, v)
    return data


def get(key, default=""):
    if key in LOCKED and LOCKED[key]:
        return LOCKED[key]
    cfg = ensure_config()
    return cfg.get(key, default) or os.environ.get(key, default)


def set_key(key, value):
    if key in LOCKED:
        raise PermissionError(f"{key} is locked and cannot be changed")
    cfg = ensure_config()
    cfg[key] = value
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")


def set_many(pairs: dict):
    cfg = ensure_config()
    blocked = []
    for k, v in pairs.items():
        if k in LOCKED:
            blocked.append(k)
            continue
        cfg[k] = v
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    return blocked


def all_keys():
    cfg = ensure_config()
    merged = dict(cfg)
    for k, v in LOCKED.items():
        if v:
            merged[k] = v
    return merged


def config_path():
    return str(CONFIG_FILE)


def apply_to_env():
    for k, v in all_keys().items():
        if v:
            os.environ[k] = str(v)


def is_first_run():
    return not CONFIG_FILE.exists()


def locked_keys():
    return list(LOCKED.keys())