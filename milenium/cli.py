import click
from rich.console import Console
from rich.table import Table
from .modules import username, email, phone, ip, domain, breach, social
import sys
from milenium.modules.logger import TeeLogger

def main():
    sys.stdout = TeeLogger("milenium.log", mode="a")
console = Console()

@click.group()
def main():
    """milenium — OSINT / dox / deanon toolkit"""
    pass

@main.command()
@click.argument("nick")
def user(nick):
    """Прогон никнейма по соцсетям"""
    results = username.check(nick)
    table = Table(title=f"Username: {nick}")
    table.add_column("Site")
    table.add_column("Status")
    for site, status in results.items():
        table.add_row(site, "[green]found[/green]" if status else "[red]no[/red]")
    console.print(table)

@main.command()
@click.argument("mail")
def mail(mail):
    """Проверка email: MX, соцсети, утечки"""
    results = email.check(mail)
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")

@main.command()
@click.argument("number")
def phone_cmd(number):
    """Инфа по номеру телефона"""
    results = phone.check(number)
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")

@main.command()
@click.argument("address")
def ip_cmd(address):
    """Гео, ASN, reverse DNS по IP"""
    results = ip.check(address)
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")

@main.command()
@click.argument("host")
def dom(host):
    """WHOIS, DNS, subdomains по домену"""
    results = domain.check(host)
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")

@main.command()
@click.argument("query")
def leaks(query):
    """Проверка утечек (HIBP, etc.)"""
    results = breach.check(query)
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")

@main.command()
@click.argument("nick")
def social_cmd(nick):
    """Поиск соцсетей по нику"""
    results = social.check(nick)
    for k, v in results.items():
        console.print(f"[bold]{k}:[/bold] {v}")

if __name__ == "__main__":
    main()