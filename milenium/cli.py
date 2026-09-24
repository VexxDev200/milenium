import sys
import json
import time
import asyncio
import click
from rich.console import Console
from rich.table import Table
from milenium.modules.logger import TeeLogger, progress
from milenium.modules import (
    neon_db, aggregator,
    shodan_search, censys_search, virustotal_search,
    abuseipdb_search, ipinfo_search, urlscan_search,
    maigret_search, sherlock_search, holehe_search,
    telegram_analysis, image_search,
    dadata_search, fssp_search, csv_db,
)

console = Console()


def _init_logger():
    logger = TeeLogger("milenium.log", mode="a")
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