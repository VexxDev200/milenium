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
)
from milenium.tui import SESSION, log_result, draw

console = Console()


def _init_logger():
    logger = TeeLogger("milenium.log", mode="a")
    sys.stdout = logger
    return logger


def _track(results):
    SESSION["queries"] += 1
    if isinstance(results, dict):
        for v in results.values():
            if isinstance(v, dict) and v.get("found"):
                SESSION["results"] += 1
                log_result(v.get("url", "found"))


@click.group()
def main():
    """milenium — OSINT / dox / deanon toolkit"""
    pass


@main.command()
@click.argument("nick")
@click.option("--permutations", default=30, help="Сколько вариаций генерить")
@click.option("--dorks/--no-dorks", default=True, help="Искать через Google Dorks")
def user(nick, permutations, dorks):
    """Глубокий поиск по нику + вариации + Google Dorks"""
    logger = _init_logger()
    lines = [f"=== DEEP SEARCH: {nick} ===", f"Permutations: {permutations}", ""]

    console.print("[bold cyan]Генерирую вариации...[/bold cyan]")
    results = username.check(nick, permutations=permutations)
    _track(results)

    table = Table(title=f"Username: {nick} (+ {len(results)-1} вариаций)")
    table.add_column("Вариация")
    table.add_column("Сайт")
    table.add_column("Статус")
    table.add_column("URL")

    found_count = 0
    for variant, sites in results.items():
        for site, info in sites.items():
            if info["found"]:
                table.add_row(variant, site, "[green]FOUND[/green]", info["url"])
                lines.append(f"{variant}\t{site}\tFOUND\t{info['url']}")
                found_count += 1

    console.print(table)
    console.print(f"[bold green]Найдено: {found_count}[/bold green]")
    lines.append(f"\nTotal found: {found_count}")

    if dorks:
        console.print("\n[bold cyan]Ищу через Google Dorks...[/bold cyan]")
        dork_results = dorker.search_nick(nick, num=10)
        if dork_results:
            for q, links in dork_results.items():
                console.print(f"\n[bold]{q}[/bold]")
                lines.append(f"\nQUERY: {q}")
                for link in links:
                    console.print(f"  {link}")
                    lines.append(f"  {link}")
        else:
            console.print("[yellow]Serper API не настроен[/yellow]")

    path = report.save_text(lines, name=f"deep_{nick}")
    console.print(f"\n[bold cyan]Отчёт:[/bold cyan] {path}")
    console.print(f"[bold cyan]Лог:[/bold cyan] {logger.path}")
    logger.close()


@main.command()
@click.argument("mail")
def mail(mail):
    """Проверка email: MX, HIBP, Gravatar"""
    logger = _init_logger()
    results = email.check(mail)
    _track(results)
    lines = [f"Email: {mail}"]
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")
        lines.append(f"{k}: {v}")
    path = report.save_text(lines, name=f"mail_{mail.split('@')[0]}")
    console.print(f"\n[bold cyan]Отчёт:[/bold cyan] {path}")
    logger.close()


@main.command()
@click.argument("number")
def phone_cmd(number):
    """Инфа по номеру телефона"""
    logger = _init_logger()
    results = phone.check(number)
    lines = [f"Phone: {number}"]
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")
        lines.append(f"{k}: {v}")
    path = report.save_text(lines, name=f"phone_{number.replace('+','')}")
    console.print(f"\n[bold cyan]Отчёт:[/bold cyan] {path}")
    logger.close()


@main.command()
@click.argument("address")
def ip_cmd(address):
    """Гео, ASN, reverse DNS, Shodan, репутация"""
    logger = _init_logger()
    results = ip.check(address)
    results["shodan"] = shodan_lite.check_ip(address)
    results["reputation"] = ip_reputation.check(address)
    _track(results)
    lines = [f"IP: {address}"]
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")
        lines.append(f"{k}: {v}")
    path = report.save_text(lines, name=f"ip_{address.replace('.','_')}")
    console.print(f"\n[bold cyan]Отчёт:[/bold cyan] {path}")
    logger.close()


@main.command()
@click.argument("host")
def dom(host):
    """WHOIS, DNS, subdomains, crt.sh"""
    logger = _init_logger()
    results = domain.check(host)
    results["crt"] = dns_history.check(host)
    _track(results)
    lines = [f"Domain: {host}"]
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")
        lines.append(f"{k}: {v}")
    path = report.save_text(lines, name=f"dom_{host.replace('.','_')}")
    console.print(f"\n[bold cyan]Отчёт:[/bold cyan] {path}")
    logger.close()


@main.command()
@click.argument("query")
def leaks(query):
    """Проверка утечек (HIBP, etc.)"""
    logger = _init_logger()
    results = breach.check(query)
    lines = [f"Leaks: {query}"]
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")
        lines.append(f"{k}: {v}")
    path = report.save_text(lines, name=f"leaks_{query.split('@')[0]}")
    console.print(f"\n[bold cyan]Отчёт:[/bold cyan] {path}")
    logger.close()


@main.command()
@click.argument("nick")
def social_cmd(nick):
    """Поиск соцсетей по нику"""
    logger = _init_logger()
    results = social.check(nick)
    _track(results)
    lines = [f"Social: {nick}"]
    for site, info in results.items():
        status = "FOUND" if info["found"] else "NO"
        console.print(f"[bold]{site}:[/bold] {status} — {info['url']}")
        lines.append(f"{site}\t{status}\t{info['url']}")
    path = report.save_text(lines, name=f"social_{nick}")
    console.print(f"\n[bold cyan]Отчёт:[/bold cyan] {path}")
    logger.close()


@main.command()
@click.argument("password")
def pwned(password):
    """Проверить пароль через Pwned Passwords (бесплатно)"""
    logger = _init_logger()
    res = pwned_passwords.check_password(password)
    if res.get("pwned"):
        console.print(f"[red]ПАРОЛЬ В УТЕЧКАХ[/red] — встречается {res['count']} раз")
    elif "error" in res:
        console.print(f"[yellow]Ошибка:[/yellow] {res['error']}")
    else:
        console.print("[green]Пароль не найден в утечках[/green]")
    logger.close()


@main.command()
@click.argument("channel")
def telegram(channel):
    """Парсинг публичного Telegram-канала"""
    logger = _init_logger()
    res = telegram_osint.check_channel(channel)
    for k, v in res.items():
        console.print(f"[bold]{k}:[/bold] {v}")
    logger.close()


@main.command()
@click.option("--email", default=None)
@click.option("--username", default=None)
@click.option("--phone", default=None)
@click.option("--password", default=None)
@click.option("--db-path", default=None, help="Путь к локальной базе BreachCompilation")
def full(email, username, phone, password, db_path):
    """Агрегатор: гоняет запрос по всем модулям"""
    logger = _init_logger()
    res = aggregator.run(email=email, username=username, phone=phone,
                         password=password, db_path=db_path)
    console.print(json.dumps(res, indent=2, ensure_ascii=False))
    path = report.save_text([json.dumps(res, indent=2, ensure_ascii=False)], name="full")
    console.print(f"\n[bold cyan]Отчёт:[/bold cyan] {path}")
    console.print(f"[bold cyan]Лог:[/bold cyan] {logger.path}")
    logger.close()


@main.command()
def tui():
    """Интерактивный TUI-интерфейс"""
    interactive()


def interactive():
    from milenium.tui import interactive as tui_interactive
    tui_interactive()


if __name__ == "__main__":
    main()