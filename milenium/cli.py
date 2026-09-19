import sys
import click
from rich.console import Console
from rich.table import Table
from milenium.modules.logger import TeeLogger
from milenium.modules import username, email, phone, ip, domain, breach, social, report

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
def user(nick):
    """Прогон никнейма по соцсетям"""
    logger = _init_logger()
    results = username.check(nick)

    table = Table(title=f"Username: {nick}")
    table.add_column("Site")
    table.add_column("Status")
    table.add_column("URL")
    lines = [f"Username: {nick}"]

    for site, info in results.items():
        status = "[green]found[/green]" if info["found"] else "[red]no[/red]"
        table.add_row(site, status, info["url"])
        lines.append(f"{site}\t{'FOUND' if info['found'] else 'NO'}\t{info['url']}")

    console.print(table)
    path = report.save_text(lines, name=f"user_{nick}")
    console.print(f"\n[bold cyan]Отчёт сохранён:[/bold cyan] {path}")
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

@main.command()
@click.argument("password")
def pwned(password):
    """Проверить пароль через Pwned Passwords (бесплатно)"""
    logger = _init_logger()
    from milenium.modules import pwned_passwords
    res = pwned_passwords.check_password(password)
    if res.get("pwned"):
        console.print(f"[red]ПАРОЛЬ В УТЕЧКАХ[/red] — встречается {res['count']} раз")
    elif "error" in res:
        console.print(f"[yellow]Ошибка:[/yellow] {res['error']}")
    else:
        console.print("[green]Пароль не найден в утечках[/green]")
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
    from milenium.modules import aggregator
    import json
    res = aggregator.run(email=email, username=username, phone=phone,
                         password=password, db_path=db_path)
    console.print(json.dumps(res, indent=2, ensure_ascii=False))
    path = report.save_text([json.dumps(res, indent=2, ensure_ascii=False)], name="full")
    console.print(f"\n[bold cyan]Отчёт:[/bold cyan] {path}")
    console.print(f"[bold cyan]Лог:[/bold cyan] {logger.path}")
    logger.close()

if __name__ == "__main__":
    main()