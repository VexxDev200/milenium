import subprocess

import sys

import importlib



from milenium.constants import __version__, TG_LIBRARY_TARGET, DATA_DIR, ensure_layout



ensure_layout()



from milenium.library import (

    paths,

    tools,

    modules,

    databases,

    load_module,

    run_osint,

    sync_library,

    grab_tg,

    grab_best,

    build_library,

    build_library_full,

    scan_tg_folder,

    search_tg_channels,

    reupload_to_library,

    csv_import,

    csv_search,

    csv_exact,

    csv_stats,

    neon_stats,

    neon_query,

)





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



__all__ = [

    "__version__",

    "TG_LIBRARY_TARGET",

    "DATA_DIR",

    "ensure_layout",

    "paths",

    "tools",

    "modules",

    "databases",

    "load_module",

    "run_osint",

    "sync_library",

    "grab_tg",

    "grab_best",

    "build_library",

    "build_library_full",

    "scan_tg_folder",

    "search_tg_channels",

    "reupload_to_library",

    "csv_import",

    "csv_search",

    "csv_exact",

    "csv_stats",

    "neon_stats",

    "neon_query",

]


