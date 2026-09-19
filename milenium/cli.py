import sys
import json
import click
from rich.console import Console
from rich.table import Table
from milenium.modules.logger import TeeLogger
from milenium.modules import (
    username, email, phone, ip, domain, breach, social, report,
    dorker, pwned_passwords, breach_local, hibp, dehashed, leakcheck,
    aggregator, shodan_lite, ip_reputation, dns_history, telegram_osint,
    neon_db,
)

console = Console()


def _init_logger():
    logger = TeeLogger("milenium.log", mode="a")
    sys.stdout = logger
    return logger


def _save_neon(command, target, module, data, target_type=None):
    try:
        neon_db.init()
        neon_db.save(command, target, module, data, target_type=target_type)
    except Exception:
        pass


@click.group()
def main():
    """milenium — OSINT toolkit"""
    pass


@main.command()
@click.argument("nick")
@click.option("--permutations", default=30)
@click.option("--dorks/--no-dorks", default=True)
def user(nick, permutations, dorks):
    """Глубокий поиск по нику"""
    logger = _init_logger()
    results = username.check(nick, permutations=permutations)
    _save_neon("user", nick, "username", results, target_type="username")

    table = Table(title=f"Username: {nick}")
    table.add_column("Вариация")
    table.add_column("Сайт")
    table.add_column("Статус")
    table.add_column("URL")
    found = 0
    for variant, sites in results.items():
        for site, info in sites.items():
            if info["found"]:
                table.add_row(variant, site, "[green]FOUND[/green]", info["url"])
                found += 1
    console.print(table)
    console.print(f"[bold green]Найдено: {found}[/bold green]")

    if dorks:
        d = dorker.search_nick(nick, num=10)
        for q, links in d.items():
            console.print(f"\n[bold]{q}[/bold]")
            for link in links:
                console.print(f"  {link}")

    logger.close()


@main.command()
@click.argument("mail")
def mail(mail):
    """Проверка email"""
    logger = _init_logger()
    results = email.check(mail)
    _save_neon("mail", mail, "email", results, target_type="email")
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")
    logger.close()


@main.command()
@click.argument("number")
def phone_cmd(number):
    """Инфа по номеру"""
    logger = _init_logger()
    results = phone.check(number)
    _save_neon("phone", number, "phone", results, target_type="phone")
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")
    logger.close()


@main.command()
@click.argument("address")
def ip_cmd(address):
    """Гео, ASN, Shodan, репутация"""
    logger = _init_logger()
    results = ip.check(address)
    results["shodan"] = shodan_lite.check_ip(address)
    results["reputation"] = ip_reputation.check(address)
    _save_neon("ip", address, "ip", results, target_type="ip")
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")
    logger.close()


@main.command()
@click.argument("host")
def dom(host):
    """WHOIS, DNS, crt.sh"""
    logger = _init_logger()
    results = domain.check(host)
    results["crt"] = dns_history.check(host)
    _save_neon("dom", host, "domain", results, target_type="domain")
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")
    logger.close()


@main.command()
@click.argument("query")
def leaks(query):
    """HIBP утечки"""
    logger = _init_logger()
    results = breach.check(query)
    _save_neon("leaks", query, "breach", results, target_type="email")
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")
    logger.close()


@main.command()
@click.argument("nick")
def social_cmd(nick):
    """Поиск соцсетей"""
    logger = _init_logger()
    results = social.check(nick)
    _save_neon("social", nick, "social", results, target_type="username")
    for site, info in results.items():
        status = "FOUND" if info["found"] else "NO"
        console.print(f"[bold]{site}:[/bold] {status} — {info['url']}")
    logger.close()


@main.command()
@click.argument("password")
def pwned(password):
    """Проверка пароля"""
    logger = _init_logger()
    res = pwned_passwords.check_password(password)
    if res.get("pwned"):
        console.print(f"[red]ПАРОЛЬ В УТЕЧКАХ[/red] — {res['count']} раз")
    elif "error" in res:
        console.print(f"[yellow]Ошибка:[/yellow] {res['error']}")
    else:
        console.print("[green]Не найден[/green]")
    logger.close()


@main.command()
@click.argument("channel")
def telegram(channel):
    """Парсинг TG-канала"""
    logger = _init_logger()
    res = telegram_osint.check_channel(channel)
    _save_neon("telegram", channel, "telegram", res, target_type="channel")
    for k, v in res.items():
        console.print(f"[bold]{k}:[/bold] {v}")
    logger.close()


@main.command()
@click.option("--email", default=None)
@click.option("--username", default=None)
@click.option("--phone", default=None)
@click.option("--password", default=None)
@click.option("--db-path", default=None)
def full(email, username, phone, password, db_path):
    """Агрегатор"""
    logger = _init_logger()
    res = aggregator.run(email=email, username=username, phone=phone,
                         password=password, db_path=db_path)
    target = email or username or phone or "unknown"
    _save_neon("full", target, "aggregator", res, target_type="mixed")
    console.print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    logger.close()


@main.command()
@click.option("--target", default=None)
@click.option("--module", default=None)
@click.option("--limit", default=50)
@click.option("--stats", is_flag=True)
def db_neon(target, module, limit, stats):
    """NeonDB работа"""
    logger = _init_logger()
    try:
        neon_db.init()
        if stats:
            s = neon_db.stats()
            console.print(f"[bold]Всего:[/bold] {s['total']}")
            console.print(f"[bold]Findings:[/bold] {s['findings']}")
            console.print(f"[bold]Leaks:[/bold] {s['leaks']}")
            for m, c in s["by_module"].items():
                console.print(f"  [red]{m}[/red]: {c}")
        else:
            rows = neon_db.query(target=target, module=module, limit=limit)
            table = Table(title="NeonDB")
            table.add_column("Время")
            table.add_column("Команда")
            table.add_column("Цель")
            table.add_column("Тип")
            table.add_column("Модуль")
            table.add_column("Найдено")
            for r in rows:
                table.add_row(str(r["ts"])[:19], r["command"], r["target"],
                              r["target_type"] or "", r["module"], str(r["found_count"]))
            console.print(table)
    except Exception as e:
        console.print(f"[bold red]Ошибка Neon:[/bold red] {e}")
    logger.close()


@main.command()
@click.option("--target", default=None)
@click.option("--limit", default=100)
def db_findings(target, limit):
    """Найденные ссылки"""
    logger = _init_logger()
    try:
        rows = neon_db.findings(target=target, limit=limit)
        table = Table(title="Findings")
        table.add_column("Время")
        table.add_column("Цель")
        table.add_column("Источник")
        table.add_column("URL")
        table.add_column("Найдено")
        for r in rows:
            table.add_row(str(r["ts"])[:19], r["target"], r["source"],
                          r["url"] or "", "[green]YES[/green]" if r["found"] else "[red]NO[/red]")
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Ошибка:[/bold red] {e}")
    logger.close()


@main.command()
@click.option("--target", default=None)
@click.option("--limit", default=100)
def db_leaks(target, limit):
    """Утечки из NeonDB"""
    logger = _init_logger()
    try:
        rows = neon_db.leaks(target=target, limit=limit)
        table = Table(title="Leaks")
        table.add_column("Время")
        table.add_column("Цель")
        table.add_column("Email")
        table.add_column("Пароль")
        table.add_column("Источник")
        table.add_column("Утечка")
        for r in rows:
            table.add_row(str(r["ts"])[:19], r["target"], r["email"] or "",
                          r["password"] or "", r["source"] or "", r["breach"] or "")
        console.print(table)
    except Exception as e:
        console.print(f"[bold red]Ошибка:[/bold red] {e}")
    logger.close()


@main.command()
def tui():
    """TUI-интерфейс"""
    from milenium.tui import interactive
    interactive()


if __name__ == "__main__":
    main()