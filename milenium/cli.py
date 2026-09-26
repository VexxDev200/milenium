import sys
import json
import time
import asyncio
import click
from rich.console import Console
from rich.table import Table

from milenium.constants import (
    ensure_layout,
    TG_DUMPS_DIR,
    TG_ACCOUNTS_FILE,
    TG_ACCOUNTS_4_FILE,
    TG_FOLDER_SCAN_JSON,
    TG_SEARCH_JSON,
    TG_LIBRARY_TARGET,
    NEON_LOG,
)
ensure_layout()
from milenium.modules import config

config.apply_to_env()

from milenium.modules.logger import TeeLogger, progress
from milenium.modules import (
    neon_db, aggregator,
    shodan_search, censys_search, virustotal_search,
    abuseipdb_search, ipinfo_search, urlscan_search,
    maigret_search, sherlock_search, holehe_search,
    telegram_analysis, image_search,
    dadata_search, fssp_search, csv_db, tg_scraper, tg_searcher, tg_reupload, tg_folder_scanner,
)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    try:
        sys.__stdout__.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console()


def _init_logger():
    logger = TeeLogger(str(NEON_LOG), mode="a")
    sys.stdout = logger
    return logger


def _save(command, target, module, data, target_type=None):
    try:
        neon_db.init()
        neon_db.save(command, target, module, data, target_type=target_type)
        progress("NeonDB: записано")
    except Exception as e:
        progress(f"NeonDB error: {e}")


@click.group()
def main():
    """milenium — OSINT агрегатор"""
    pass


@main.command()
@click.argument("username")
def user(username):
    """Maigret + Sherlock"""
    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: user {username}")
    res = aggregator.run(username=username)
    _save("user", username, "username", res, "username")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()

@main.command()
@click.argument("query")
def leak(query):
    """Поиск по базам утечек (NiamonX + HIBP)"""
    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: leak {query}")
    from milenium.modules import leak_search
    nia = asyncio.run(leak_search.niamonx_search(query))
    hibp = asyncio.run(leak_search.hibp_test(query))
    res = {"niamonx": nia, "hibp": hibp}
    _save("leak", query, "leak", res, "leak")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()

@main.command()
@click.argument("email")
def email_cmd(email):
    """Holehe + VirusTotal domain"""
    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: email {email}")
    res = aggregator.run(email=email)
    _save("email", email, "email", res, "email")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@main.command()
@click.argument("ip")
def ip_cmd(ip):
    """Shodan + Censys + VT + AbuseIPDB + ipinfo"""
    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: ip {ip}")
    res = aggregator.run(ip=ip)
    _save("ip", ip, "ip", res, "ip")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@main.command()
@click.argument("url")
def url_cmd(url):
    """urlscan.io анализ"""
    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: url {url}")
    res = aggregator.run(url=url)
    _save("url", url, "url", res, "url")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@main.command()
@click.argument("username")
def tg(username):
    """Telethon: TG-аккаунт"""
    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: telegram {username}")
    res = asyncio.run(telegram_analysis.check_user(username))
    _save("telegram", username, "telegram", res, "username")
    for k, v in res.items():
        console.print(f"[bold]{k}:[/bold] {v}")
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@main.command()
@click.argument("image_path")
@click.option("--engine", default="yandex")
def img(image_path, engine):
    """PicImageSearch: обратный поиск по фото"""
    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: image {engine}")
    res = asyncio.run(image_search.search(image_path, engine))
    _save("image", image_path, "image", res, "file")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@main.command()
@click.argument("query")
def company(query):
    """DaData: поиск компании по ИНН/ОГРН/названию"""
    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: company {query}")
    res = asyncio.run(dadata_search.search_company(query))
    _save("company", query, "dadata", res, "company")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@main.command()
@click.argument("phone")
def phone_info(phone):
    """DaData: оператор и регион по номеру"""
    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: phone {phone}")
    res = asyncio.run(dadata_search.search_phone(phone))
    _save("phone", phone, "dadata", res, "phone")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@main.command()
@click.option("--first", required=True)
@click.option("--last", required=True)
@click.option("--birth", required=True)
@click.option("--region", default=0)
def fssp(first, last, birth, region):
    """ФССП: поиск долгов"""
    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: fssp {first} {last}")
    res = asyncio.run(fssp_search.check_physical(first, last, birth, region))
    _save("fssp", f"{first} {last}", "fssp", res, "person")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@main.command()
@click.option("--target", default=None)
@click.option("--stats", is_flag=True)
def db_neon(target, stats):
    """NeonDB статистика и поиск"""
    logger = _init_logger()
    try:
        neon_db.init()
        if stats:
            s = neon_db.stats()
            console.print(f"[bold]Всего:[/bold] {s['total']}")
            console.print(f"[bold]Findings:[/bold] {s['findings']}")
            console.print(f"[bold]Leaks:[/bold] {s['leaks']}")
        else:
            rows = neon_db.query(target=target, limit=50)
            table = Table(title="NeonDB")
            table.add_column("Время")
            table.add_column("Команда")
            table.add_column("Цель")
            table.add_column("Модуль")
            for r in rows:
                table.add_row(str(r["ts"])[:19], r["command"], r["target"], r["module"])
            console.print(table)
    except Exception as e:
        console.print(f"[bold red]Ошибка Neon:[/bold red] {e}")
    logger.close()


@main.command()
@click.option("--key", default=None)
@click.option("--value", default=None)
def config_cmd(key, value):
    """Просмотр и настройка конфига"""
    from milenium.modules import config
    if key and value:
        try:
            config.set_key(key, value)
            console.print(f"[green]Сохранено:[/green] {key}")
        except PermissionError as e:
            console.print(f"[red]LOCKED:[/red] {e}")
        return
    cfg = config.all_keys()
    locked = config.locked_keys()
    console.print(f"[bold]Конфиг:[/bold] {config.config_path()}")
    console.print(f"[bold red]LOCKED:[/bold red] {', '.join(locked)}")
    for k, v in cfg.items():
        if k in locked:
            console.print(f"  [red]{k}[/red] = 🔒 [LOCKED]")
        else:
            shown = (v[:8] + "...") if v and len(v) > 12 else (v or "[empty]")
            console.print(f"  [white]{k}[/white] = {shown}")


@main.command(name="tg_reupload")
@click.argument("local_dir", default=None)
@click.option("--target", default=None, show_default=str(TG_LIBRARY_TARGET), help="TG-канал для заливки")
@click.option("--keep", is_flag=True, help="Не удалять локальные файлы после отправки")
@click.option("--accounts-file", default=None, show_default=str(TG_ACCOUNTS_FILE), help="JSON/CSV с аккаунтами")
def tg_reupload_cmd(local_dir, target, keep, accounts_file):
    """Переотправить локальные файлы в TG-канал"""
    logger = _init_logger()
    t0 = time.time()
    local_dir = local_dir or str(TG_DUMPS_DIR)
    target = target or TG_LIBRARY_TARGET
    accounts_file = accounts_file or str(TG_ACCOUNTS_FILE)
    progress(f"старт: tg_reupload {local_dir} → {target}")
    res = tg_reupload.run_reupload(local_dir=local_dir, accounts_file=accounts_file, target=target, delete_after=not keep)
    _save("tg_reupload", local_dir, "tg_reupload", res, target_type="telegram")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@main.command(name="tg_search")
@click.argument("queries", nargs=-1, required=False)
@click.option("--accounts-file", default=None, show_default=str(TG_ACCOUNTS_FILE), help="JSON/CSV с аккаунтами")
@click.option("--limit", default=200, show_default=True, help="Сообщений на запрос")
@click.option("--min-mentions", default=1, show_default=True, help="Минимальное число упоминаний канала")
@click.option("--no-check-files", is_flag=True, help="Не проверять наличие файлов в канале")
@click.option("--file-sample", default=5, show_default=True, help="Сколько файлов проверять в канале")
@click.option("--output", default=None, show_default=str(TG_SEARCH_JSON), help="Файл результатов")
def tg_search(queries, accounts_file, limit, min_mentions, no_check_files, file_sample, output):
    """Поиск публичных TG-каналов с базами/сливами. Без запросов — использует встроенный список."""
    logger = _init_logger()
    t0 = time.time()
    accounts_file = accounts_file or str(TG_ACCOUNTS_FILE)
    output = output or str(TG_SEARCH_JSON)
    query_list = list(queries) if queries else None
    progress(f"старт: tg_search {len(query_list) if query_list else 'default'} запросов")
    res = tg_searcher.run(
        queries=query_list,
        accounts_file=accounts_file,
        limit_per_query=limit,
        min_mentions=min_mentions,
        check_files=not no_check_files,
        file_sample=file_sample,
        output=output,
    )
    _save("tg_search", str(len(query_list) if query_list else "default"), "tg_searcher", res, target_type="telegram")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@main.command(name="tg_scan_folder")
@click.argument("folder_name")
@click.option("--accounts-file", default=None, show_default=str(TG_ACCOUNTS_4_FILE), help="JSON/CSV с аккаунтами")
@click.option("--sample", default=50, show_default=True, help="Сколько файлов проверять в канале/топике")
@click.option("--min-bases", default=1, show_default=True, help="Минимальное число баз в отчёте")
@click.option("--max-topics", default=120, show_default=True, help="Макс топиков на форум-канал")
@click.option("--channel-timeout", default=240, show_default=True, help="Секунд на канал, потом skip")
@click.option("--output", default=None, show_default=str(TG_FOLDER_SCAN_JSON), help="Файл отчёта")
def tg_scan_folder(folder_name, accounts_file, sample, min_bases, max_topics, channel_timeout, output):
    """Сканировать папку TG и показать, в каких каналах есть базы данных"""
    logger = _init_logger()
    t0 = time.time()
    accounts_file = accounts_file or str(TG_ACCOUNTS_4_FILE)
    output = output or str(TG_FOLDER_SCAN_JSON)
    progress(f"старт: tg_scan_folder '{folder_name}'")
    res = tg_folder_scanner.run(
        folder_name=folder_name,
        accounts_file=accounts_file,
        sample_limit=sample,
        min_bases=min_bases,
        max_topics=max_topics,
        channel_timeout=channel_timeout,
        output=output,
    )
    _save("tg_scan_folder", folder_name, "tg_folder_scanner", res, target_type="telegram")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@main.group()
def library():
    """Библиотека milenium — TG-архив, локальные базы, реестр инструментов"""
    pass


@library.command("sync")
@click.option("--folder", default="бд", show_default=True)
@click.option("--accounts-file", default=None, help=f"По умолчанию {TG_ACCOUNTS_FILE}")
@click.option("--limit", default=100000, show_default=True)
@click.option("--topics", default=None)
@click.option("--use-four-accounts", is_flag=True)
def library_sync(folder, accounts_file, limit, topics, use_four_accounts):
    """Синхронизация: invite + папка TG → архив milenium"""
    from milenium.library import sync_library

    logger = _init_logger()
    t0 = time.time()
    topic_patterns = [t.strip() for t in topics.split(",")] if topics else None
    progress(f"старт: library sync → папка «{folder}»")
    res = sync_library(
        folder=folder,
        accounts_file=accounts_file,
        limit_per_channel=limit,
        topic_patterns=topic_patterns,
        use_four_accounts=use_four_accounts,
    )
    _save("library_sync", folder, "library", res, target_type="telegram")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@library.command("grab-best")
@click.option("--folder", default="бд", show_default=True, help="Папка TG")
@click.option("--min-size-mb", default=50, show_default=True, help="Минимальный размер базы в MB")
@click.option("--max-files", default=100, show_default=True, help="Сколько лучших файлов выкачать")
@click.option("--accounts-file", default=None, help=f"По умолчанию {TG_ACCOUNTS_FILE}")
@click.option("--use-four-accounts", is_flag=True, help="Только 4 аккаунта")
@click.option("--no-upload", is_flag=True, help="Только скачать локально")
def library_grab_best(folder, min_size_mb, max_files, accounts_file, use_four_accounts, no_upload):
    """Скачать лучшие базы + тулки из TG в архив milenium"""
    from milenium.library import grab_best

    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: library grab-best — базы >= {min_size_mb}MB, топ {max_files}")
    res = grab_best(
        folder=folder,
        accounts_file=accounts_file,
        min_size_mb=min_size_mb,
        max_files=max_files,
        use_four_accounts=use_four_accounts,
        no_upload=no_upload,
    )
    _save("library_grab_best", folder, "tg_best_grab", res, target_type="telegram")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@library.command("build")
@click.option("--folder", default="бд", show_default=True)
@click.option("--min-size-mb", default=50, show_default=True)
@click.option("--max-files", default=200, show_default=True)
@click.option("--use-four-accounts", is_flag=True)
@click.option("--no-upload", is_flag=True)
def library_build(folder, min_size_mb, max_files, use_four_accounts, no_upload):
    """Standalone builder: лучшие базы + тулки → архив"""
    from milenium.library import build_library

    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: library build — базы >= {min_size_mb}MB, топ {max_files}")
    res = build_library(
        folder=folder,
        min_size_mb=min_size_mb,
        max_files=max_files,
        use_four_accounts=use_four_accounts,
        no_upload=no_upload,
    )
    _save("library_build", folder, "build_library", res, target_type="telegram")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@library.command("build-full")
@click.option("--folder", default="бд", show_default=True)
@click.option("--min-size-mb", default=50, show_default=True)
@click.option("--max-files", default=500, show_default=True)
@click.option("--use-four-accounts", is_flag=True)
@click.option("--no-upload", is_flag=True)
def library_build_full(folder, min_size_mb, max_files, use_four_accounts, no_upload):
    """Полная сборка: скан + поиск + grab-best"""
    from milenium.library import build_library_full

    logger = _init_logger()
    t0 = time.time()
    progress("старт: library build-full — скан, поиск, grab-best")
    res = build_library_full(
        folder=folder,
        min_size_mb=min_size_mb,
        max_files=max_files,
        use_four_accounts=use_four_accounts,
        no_upload=no_upload,
    )
    _save("library_build_full", folder, "build_library_full", res, target_type="telegram")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@library.command("tools")
def library_tools_cmd():
    """Список всех инструментов milenium"""
    from milenium.library import tools as _tools

    reg = _tools()
    for cat, items in reg.items():
        console.print(f"\n[bold cyan]{cat.upper()}[/bold cyan]")
        for cmd, desc in items.items():
            console.print(f"  [white]milenium {cmd}[/white] — {desc}")


@library.command("modules")
@click.option("--flat", is_flag=True, help="Плоский список")
def library_modules_cmd(flat):
    """Все Python-модули пакета (~60)"""
    from milenium.library import modules as _modules
    from milenium.registry import module_count

    data = _modules(flat=flat)
    if flat:
        console.print(f"[dim]модулей: {module_count()}[/dim]")
        console.print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        console.print(f"[bold]Модулей:[/bold] {module_count()}")
        for cat, mods in data.items():
            console.print(f"\n[bold cyan]{cat}[/bold cyan] ({len(mods)})")
            for name, meta in mods.items():
                console.print(f"  [white]{name}[/white] — {meta['desc']}")


@library.command("databases")
@click.option("--no-scan", is_flag=True, help="Не сканировать файлы в data/")
def library_databases_cmd(no_scan):
    """Neon, CSV SQLite, tg_dumps, отчёты"""
    from milenium.library import databases as _db

    info = _db(include_scan=not no_scan)
    console.print(json.dumps(info, indent=2, ensure_ascii=False, default=str))


@library.command("paths")
def library_paths_cmd():
    """Пути data/ и TG-архив"""
    from milenium.library import paths as _paths

    console.print(json.dumps(_paths(), indent=2, ensure_ascii=False))


MILENIUM_LIBRARY_LINKS = (
    "https://t.me/+J-d1E0GyCiA3NmRi",
    "https://t.me/+mFFLoewnHoNjZWQy",
    "https://t.me/+3RnTj-8fCSs5OWQ0",
    "https://t.me/+jI4gCRn51Ro0ZTdi",
)


@main.command(name="tg_library")
@click.argument("extra_links", nargs=-1, required=False)
@click.option("--folder", default="бд", show_default=True)
@click.option("--accounts-file", default=None)
@click.option("--output", default=None, show_default=str(TG_DUMPS_DIR))
@click.option("--limit", default=100000, show_default=True)
@click.option("--topics", default=None)
@click.option("--use-four-accounts", is_flag=True)
def tg_library(extra_links, folder, accounts_file, output, limit, topics, use_four_accounts):
    """Alias: library sync (источники + папка «бд» → архив)"""
    from milenium.library import sync_library

    logger = _init_logger()
    t0 = time.time()
    topic_patterns = [t.strip() for t in topics.split(",")] if topics else None
    output = output or str(TG_DUMPS_DIR)
    progress(f"старт: tg_library / library sync")
    res = sync_library(
        folder=folder,
        extra_links=list(extra_links) if extra_links else None,
        accounts_file=accounts_file,
        limit_per_channel=limit,
        topic_patterns=topic_patterns,
        use_four_accounts=use_four_accounts,
        output_dir=output,
    )
    _save("tg_library", folder, "library", res, target_type="telegram")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@main.command(name="tg_grab")
@click.argument("links", nargs=-1, required=False)
@click.option("--accounts-file", default=None, show_default=str(TG_ACCOUNTS_FILE), help="JSON/CSV с аккаунтами")
@click.option("--output", default=None, show_default=str(TG_DUMPS_DIR))
@click.option("--limit", default=500, show_default=True, help="Сообщений на канал")
@click.option("--max-file-mb", default=0, show_default=True, help="Макс размер файла MB (0 = без лимита)")
@click.option("--rclone-remote", default=None, help="Rclone remote:path для синхронизации")
@click.option("--rclone-bin", default=None, help="Путь к rclone.exe (если не в PATH)")
@click.option("--gdrive-service-account", default=None, help="Путь к service_account.json Google Drive")
@click.option("--gdrive-folder", default="milenium_tg_dumps", show_default=True, help="Имя папки на Google Drive")
@click.option("--tg-upload-target", default=None, help="TG-получатель файлов (me / username / channel id)")
@click.option("--no-upload", is_flag=True, help="Только скачать локально, не загружать в облако")
@click.option("--delete-local", is_flag=True, help="Удалить локальные файлы после загрузки в облако")
@click.option("--topics", default=None, help="Скачивать только указанные топики (через запятую)")
@click.option("--folder", default=None, help="Скачать все каналы из папки TG по названию")
def tg_grab(links, accounts_file, output, limit, max_file_mb, rclone_remote, rclone_bin, gdrive_service_account, gdrive_folder, tg_upload_target, no_upload, delete_local, topics, folder):
    """Войти в TG-каналы/папку и скачать базы (CSV/SQLITE/архивы)"""
    if not links and not folder:
        console.print("[red]Укажи ссылки или --folder[/red]")
        return
    logger = _init_logger()
    t0 = time.time()
    accounts_file = accounts_file or str(TG_ACCOUNTS_FILE)
    output = output or str(TG_DUMPS_DIR)
    topic_patterns = [t.strip() for t in topics.split(",")] if topics else None
    progress(f"старт: tg_grab {len(links)} каналов" + (f" [топики: {topics}]" if topics else "") + (f" [папка: {folder}]" if folder else ""))
    res = tg_scraper.run(
        links=list(links) if links else None,
        accounts_file=accounts_file,
        output_dir=output,
        limit_per_channel=limit,
        max_file_mb=max_file_mb,
        rclone_remote=rclone_remote,
        rclone_bin=rclone_bin,
        gdrive_service_account=gdrive_service_account,
        gdrive_folder=gdrive_folder,
        tg_upload_target=tg_upload_target,
        no_upload=no_upload,
        delete_local=delete_local,
        topic_patterns=topic_patterns,
        folder_name=folder,
    )
    _save("tg_grab", str(len(links)), "tg_scraper", res, target_type="telegram")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@main.command()
def bot():
    """Запустить Telegram-бота"""
    from milenium.modules.tg_bot import main as bot_main
    bot_main()


@main.command()
def tui():
    """TUI интерфейс"""
    from milenium.tui import interactive
    interactive()


@main.group()
def csv():
    """Локальные CSV-базы (Instagram800K и т.п.)"""
    pass


@csv.command(name="import")
@click.argument("path")
@click.option("--force", is_flag=True)
def csv_import(path, force):
    """Импортировать CSV в SQLite с индексами"""
    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: csv import {path}")
    db_path = csv_db.init_db(path, force=force)
    console.print(f"[green]БД готова:[/green] {db_path}")
    progress(f"готово за {time.time() - t0:.1f}s")
    logger.close()


@csv.command(name="search")
@click.argument("path")
@click.argument("query")
@click.option("--limit", default=20, show_default=True)
def csv_search(path, query, limit):
    """Поиск по CSV через FTS5 / LIKE"""
    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: csv search '{query}'")
    rows = csv_db.search(path, query, limit=limit)
    res = {"rows": rows, "count": len(rows), "db": str(csv_db.db_path(path))}
    _save("csv_search", query, "csv_db", res, target_type="csv")
    console.print(json.dumps(rows, indent=2, ensure_ascii=False, default=str))
    progress(f"готово: {len(rows)} за {time.time() - t0:.1f}s")
    logger.close()


@csv.command(name="exact")
@click.argument("path")
@click.argument("field")
@click.argument("value")
@click.option("--limit", default=20, show_default=True)
def csv_exact(path, field, value, limit):
    """Точный поиск по полю (uid/name/email/username/...)"""
    logger = _init_logger()
    t0 = time.time()
    progress(f"старт: csv exact {field}={value}")
    rows = csv_db.exact(path, field, value, limit=limit)
    res = {"rows": rows, "count": len(rows), "field": field, "value": value, "db": str(csv_db.db_path(path))}
    _save("csv_exact", f"{field}={value}", "csv_db", res, target_type="csv")
    console.print(json.dumps(rows, indent=2, ensure_ascii=False, default=str))
    progress(f"готово: {len(rows)} за {time.time() - t0:.1f}s")
    logger.close()


@csv.command(name="stats")
@click.argument("path")
def csv_stats(path):
    """Статистика по SQLite-базе CSV"""
    logger = _init_logger()
    progress(f"старт: csv stats {path}")
    s = csv_db.stats(path)
    console.print(json.dumps(s, indent=2, ensure_ascii=False, default=str))
    progress(f"готово")
    logger.close()


if __name__ == "__main__":
    main()