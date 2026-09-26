"""
Высокоуровневый API библиотеки milenium.

После pip install milenium (из любой папки):

    import milenium
    milenium.ensure_layout()
    milenium.sync_library()
"""
from pathlib import Path

from milenium.constants import (
    TG_LIBRARY_TARGET,
    TG_LIBRARY_SOURCE_LINKS,
    TG_FOLDER_DEFAULT,
    TG_ACCOUNTS_FILE,
    TG_ACCOUNTS_4_FILE,
    TG_DUMPS_DIR,
    TG_FOLDER_SCAN_JSON,
    TG_SEARCH_JSON,
    DATA_DIR,
    MILENIUM_HOME,
    CONFIG_FILE,
    NEON_LOG,
    __version__,
    ensure_layout,
    tool_registry,
)


def paths():
    """Стандартные пути (создаёт каталоги при первом вызове)."""
    ensure_layout()
    return {
        "home": str(MILENIUM_HOME),
        "config": str(CONFIG_FILE),
        "log": str(NEON_LOG),
        "data": str(DATA_DIR),
        "tg_dumps": str(TG_DUMPS_DIR),
        "tg_accounts": str(TG_ACCOUNTS_FILE),
        "tg_accounts_4": str(TG_ACCOUNTS_4_FILE),
        "tg_folder_scan": str(TG_FOLDER_SCAN_JSON),
        "tg_search_results": str(TG_SEARCH_JSON),
        "tg_library_target": TG_LIBRARY_TARGET,
    }


def tools():
    """CLI-команды пакета по категориям."""
    return tool_registry()


def modules(flat=False):
    from milenium.registry import list_modules

    return list_modules(flat=flat)


def databases(include_scan=True):
    from milenium.registry import list_databases

    ensure_layout()
    return list_databases(include_scan=include_scan)


def load_module(name: str):
    from milenium.registry import load_module as _load

    return _load(name)


def run_osint(**kwargs):
    from milenium.modules import aggregator

    return aggregator.run(**kwargs)


def sync_library(
    folder=TG_FOLDER_DEFAULT,
    extra_links=None,
    accounts_file=None,
    limit_per_channel=100_000,
    topic_patterns=None,
    use_four_accounts=False,
    output_dir=None,
):
    from milenium.modules import tg_scraper

    ensure_layout()
    links = list(TG_LIBRARY_SOURCE_LINKS)
    if extra_links:
        links.extend(extra_links)
    acc = str(TG_ACCOUNTS_4_FILE if use_four_accounts else TG_ACCOUNTS_FILE)
    if accounts_file:
        acc = accounts_file
    out = output_dir or str(TG_DUMPS_DIR)
    Path(out).mkdir(parents=True, exist_ok=True)
    return tg_scraper.run(
        links=links,
        output_dir=out,
        limit_per_channel=limit_per_channel,
        accounts_file=acc,
        tg_upload_target=TG_LIBRARY_TARGET,
        delete_local=True,
        topic_patterns=topic_patterns,
        folder_name=folder,
    )


def grab_tg(links, **kwargs):
    from milenium.modules import tg_scraper

    ensure_layout()
    kwargs.setdefault("output_dir", str(TG_DUMPS_DIR))
    kwargs.setdefault("accounts_file", str(TG_ACCOUNTS_FILE))
    return tg_scraper.run(links=list(links) if links else None, **kwargs)


def grab_best(
    folder=TG_FOLDER_DEFAULT,
    min_size_mb=50,
    max_files=100,
    accounts_file=None,
    use_four_accounts=False,
    no_upload=False,
):
    from milenium.modules import tg_best_grab

    ensure_layout()
    return tg_best_grab.run(
        folder=folder,
        accounts_file=accounts_file,
        min_size_mb=min_size_mb,
        max_files=max_files,
        use_four_accounts=use_four_accounts,
        no_upload=no_upload,
    )


def build_library(
    folder=TG_FOLDER_DEFAULT,
    min_size_mb=50,
    max_files=200,
    accounts_file=None,
    use_four_accounts=False,
    no_upload=False,
):
    """Alias grab_best — standalone builder API."""
    return grab_best(
        folder=folder,
        min_size_mb=min_size_mb,
        max_files=max_files,
        accounts_file=accounts_file,
        use_four_accounts=use_four_accounts,
        no_upload=no_upload,
    )


def build_library_full(
    folder=TG_FOLDER_DEFAULT,
    min_size_mb=50,
    max_files=500,
    accounts_file=None,
    use_four_accounts=False,
    no_upload=False,
):
    """Полная сборка: скан папки + поиск каналов + grab-best."""
    ensure_layout()
    scan = scan_tg_folder(folder, accounts_file=accounts_file)
    search = search_tg_channels(accounts_file=accounts_file)
    grab = grab_best(
        folder=folder,
        min_size_mb=min_size_mb,
        max_files=max_files,
        accounts_file=accounts_file,
        use_four_accounts=use_four_accounts,
        no_upload=no_upload,
    )
    return {
        "scan": scan,
        "search": search,
        "grab": grab,
    }


def scan_tg_folder(folder=TG_FOLDER_DEFAULT, **kwargs):
    from milenium.modules import tg_folder_scanner

    ensure_layout()
    kwargs.setdefault("accounts_file", str(TG_ACCOUNTS_4_FILE))
    kwargs.setdefault("output", str(TG_FOLDER_SCAN_JSON))
    return tg_folder_scanner.run(folder_name=folder, **kwargs)


def search_tg_channels(queries=None, **kwargs):
    from milenium.modules import tg_searcher

    ensure_layout()
    kwargs.setdefault("accounts_file", str(TG_ACCOUNTS_FILE))
    kwargs.setdefault("output", str(TG_SEARCH_JSON))
    return tg_searcher.run(queries=queries, **kwargs)


def reupload_to_library(local_dir=None, **kwargs):
    from milenium.modules import tg_reupload

    ensure_layout()
    kwargs.setdefault("local_dir", local_dir or str(TG_DUMPS_DIR))
    kwargs.setdefault("target", TG_LIBRARY_TARGET)
    kwargs.setdefault("accounts_file", str(TG_ACCOUNTS_FILE))
    return tg_reupload.run_reupload(**kwargs)


def csv_import(path, force=False):
    from milenium.modules import csv_db

    return csv_db.init_db(path, force=force)


def csv_search(path, query, limit=20):
    from milenium.modules import csv_db

    return csv_db.search(path, query, limit=limit)


def csv_exact(path, field, value, limit=20):
    from milenium.modules import csv_db

    return csv_db.exact(path, field, value, limit=limit)


def csv_stats(path):
    from milenium.modules import csv_db

    return csv_db.stats(path)


def neon_stats():
    from milenium.modules import neon_db

    neon_db.init()
    return neon_db.stats()


def neon_query(target=None, module=None, limit=50):
    from milenium.modules import neon_db

    neon_db.init()
    return neon_db.query(target=target, module=module, limit=limit)
