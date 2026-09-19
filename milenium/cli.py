import sys
import click
from rich.console import Console
from rich.table import Table
from milenium.modules.logger import TeeLogger
from milenium.modules import username, email, phone, ip, domain, breach, social, report, dorker

console = Console()

def _init_logger():
    logger = TeeLogger("milenium.log", mode="a")
    sys.stdout = logger
    return logger

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
            console.print("[yellow]Serper API не настроен или нет результатов[/yellow]")
            lines.append("\nDorks: not configured")

    path = report.save_text(lines, name=f"deep_{nick}")
    console.print(f"\n[bold cyan]Отчёт:[/bold cyan] {path}")
    console.print(f"[bold cyan]Лог:[/bold cyan] {logger.path}")
    logger.close()

@main.command()
@click.argument("mail")
def mail(mail):
    """Проверка email: MX, соцсети, утечки"""
    logger = _init_logger()
    results = email.check(mail)
    lines = [f"Email: {mail}"]
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")
        lines.append(f"{k}: {v}")
    path = report.save_text(lines, name=f"mail_{mail.split('@')[0]}")
    console.print(f"\n[bold cyan]Отчёт сохранён:[/bold cyan] {path}")
    console.print(f"[bold cyan]Лог:[/bold cyan] {logger.path}")
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
    console.print(f"\n[bold cyan]Отчёт сохранён:[/bold cyan] {path}")
    console.print(f"[bold cyan]Лог:[/bold cyan] {logger.path}")
    logger.close()

@main.command()
@click.argument("address")
def ip_cmd(address):
    """Гео, ASN, reverse DNS по IP"""
    logger = _init_logger()
    results = ip.check(address)
    lines = [f"IP: {address}"]
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")
        lines.append(f"{k}: {v}")
    path = report.save_text(lines, name=f"ip_{address.replace('.','_')}")
    console.print(f"\n[bold cyan]Отчёт сохранён:[/bold cyan] {path}")
    console.print(f"[bold cyan]Лог:[/bold cyan] {logger.path}")
    logger.close()

@main.command()
@click.argument("host")
def dom(host):
    """WHOIS, DNS, subdomains по домену"""
    logger = _init_logger()
    results = domain.check(host)
    lines = [f"Domain: {host}"]
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")
        lines.append(f"{k}: {v}")
    path = report.save_text(lines, name=f"dom_{host.replace('.','_')}")
    console.print(f"\n[bold cyan]Отчёт сохранён:[/bold cyan] {path}")
    console.print(f"[bold cyan]Лог:[/bold cyan] {logger.path}")
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
    console.print(f"\n[bold cyan]Отчёт сохранён:[/bold cyan] {path}")
    console.print(f"[bold cyan]Лог:[/bold cyan] {logger.path}")
    logger.close()

@main.command()
@click.argument("nick")
def social_cmd(nick):
    """Поиск соцсетей по нику"""
    logger = _init_logger()
    results = social.check(nick)
    lines = [f"Social: {nick}"]
    for site, info in results.items():
        status = "FOUND" if info["found"] else "NO"
        console.print(f"[bold]{site}:[/bold] {status} — {info['url']}")
        lines.append(f"{site}\t{status}\t{info['url']}")
    path = report.save_text(lines, name=f"social_{nick}")
    console.print(f"\n[bold cyan]Отчёт сохранён:[/bold cyan] {path}")
    console.print(f"[bold cyan]Лог:[/bold cyan] {logger.path}")
    logger.close()

if __name__ == "__main__":
    main()