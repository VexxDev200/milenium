import os
import json
import base64
from pathlib import Path

CONFIG_DIR = Path.home() / ".milenium"
CONFIG_FILE = CONFIG_DIR / "config.json"


def _b64(s: str) -> str:
    return base64.b64decode(s).decode()


# ═══════════════════════════════════════════════════════════
# LOCKED — вшито в код. Пользователь НЕ МОЖЕТ менять.
# base64: python -c "import base64; print(base64.b64encode(b'ЗНАЧЕНИЕ').decode())"
# ═══════════════════════════════════════════════════════════

LOCKED = {
    # База данных
    "DATABASE_URL": _b64(
        "cG9zdGdyZXNxbDovL25lb25kYl9vd25lcjpucGdfSk5Bam5UYXowVUs1QGVwLXR3aWxpZ2h0LWJhci1iMW9mZHlvdC1wb29sZXIuYy01LmV1LWNlbnRyYWwtMS5hd3MubmVvbi50ZWNoL25lb25kYj9zc2xtb2RlPXJlcXVpcmUmY2hhbm5lbF9iaW5kaW5nPXJlcXVpcmU="
    ),

    # Telegram API (Telethon)
    "TG_API_ID": "28088599",
    "TG_API_HASH": "8df5e438f9b66dba136e70a1e7a2edb4",

    # Telegram Bot
    "TG_BOT_TOKEN": _b64("ODgxMjMyMTIyNTpBQUZndEpvX2laLVFhYnFEZzJnbWdDWU1ERDJHUlhFYl9yWQ=="),
    "TG_ALLOWED_USERS": "5496853233",

    # Shodan
    "SHODAN_API_KEY": "klFb9nYLxrCeJ284OEAtuVUygwfVtgY1",

    # Censys
    "CENSYS_TOKEN": "censys_UJptWhGQ_L57vdqJiF1FQEd1VtTVArqsX",

    # VirusTotal
    "VIRUSTOTAL_API_KEY": "13d811a2ffc3cac8af9a1c7d67affea81fb598a3f07473562adf176e6ff064ab",

    # AbuseIPDB
    "ABUSEIPDB_KEY": "94db3ce71663f504837d43de1f027fdd4a6f565d5b5e946d9337100e3849679960dbca271b6c97fe",

    # ipinfo
    "IPINFO_TOKEN": "e10996b04f9159",

    # urlscan
    "URLSCAN_API_KEY": "01a0be3c-70ce-71ec-b565-33ec1081fa30",

    # Serper (Google Dorks)
    "SERPER_API_KEY": "ВСТАВЬ_СВОЙ_SERPER_КЛЮЧ",

    # DaData (компании РФ)
    "DADATA_API_KEY": "3c360bd376f3a83d5cdfe4dfe774bdda0496baee",
    "DADATA_SECRET": "610f319e925914a90692430378a42e3530f174f9",

    # ФССП (долги)
    "FSSP_TOKEN": "ВСТАВЬ_СВОЙ_FSSP_ТОКЕН",

    # NiamonX (утечки)
    "NIAMONX_API_KEY": "ВСТАВЬ_СВОЙ_NIAMONX_КЛЮЧ",

    # HIBP
    "HIBP_KEY": "00000000000000000000000000000000",
}


# Пользователь может задать только эти ключи (если хочет свои)
DEFAULTS = {
    "PREFERRED_LANG": "ru",
    "PREFERRED_REGION": "RU",
}


def ensure_config():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        CONFIG_FILE.write_text(json.dumps(DEFAULTS, indent=2, ensure_ascii=False), encoding="utf-8")
        return dict(DEFAULTS)
    try:
        data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    for k, v in DEFAULTS.items():
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