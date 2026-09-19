from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich.align import Align

console = Console()

BANNER = """
[bold cyan]
  ███╗   ███╗██╗██╗     ███████╗███╗   ██╗██╗██╗   ██╗███╗   ███╗
  ████╗ ████║██║██║     ██╔════╝████╗  ██║██║██║   ██║████╗ ████║
  ██╔████╔██║██║██║     █████╗  ██╔██╗ ██║██║██║   ██║██╔████╔██║
  ██║╚██╔╝██║██║██║     ██╔══╝  ██║╚██╗██║██║██║   ██║██║╚██╔╝██║
  ██║ ╚═╝ ██║██║███████╗███████╗██║ ╚████║██║╚██████╔╝██║ ╚═╝ ██║
  ╚═╝     ╚═╝╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝     ╚═╝
[/bold cyan]
[bold green]  OSINT / DOX / DEANON TOOLKIT  v0.4.0[/bold green]
"""

def show_banner():
    console.print(BANNER)

def show_menu():
    table = Table(title="[bold]Команды[/bold]", show_header=True, header_style="bold magenta")
    table.add_column("Команда", style="cyan")
    table.add_column("Описание", style="white")
    rows = [
        ("user <ник>", "Поиск по 17+ соцсетям + вариации + Google Dorks"),
        ("mail <email>", "MX, HIBP, Gravatar"),
        ("phone_cmd <номер>", "Оператор, страна, часовой пояс"),
        ("ip_cmd <IP>", "Гео, ASN, reverse DNS, Shodan, репутация"),
        ("dom <домен>", "WHOIS, DNS, subdomains, crt.sh"),
        ("leaks <email>", "HIBP утечки"),
        ("social_cmd <ник>", "Поиск соцсетей"),
        ("pwned <пароль>", "Проверка пароля в утечках (бесплатно)"),
        ("full --email ... --username ... --password ...", "Агрегатор всех модулей"),
        ("telegram <канал>", "Парсинг публичного Telegram-канала"),
    ]
    for cmd, desc in rows:
        table.add_row(cmd, desc)
    console.print(table)

def interactive():
    show_banner()
    show_menu()
    console.print("\n[bold yellow]Введи команду (или 'exit'):[/bold yellow]")
    while True:
        try:
            cmd = Prompt.ask("[bold cyan]milenium[/bold cyan]")
            if cmd.strip().lower() in ("exit", "quit", "q"):
                console.print("[bold red]Выход.[/bold red]")
                break
            if not cmd.strip():
                continue
            # Парсим как CLI
            import shlex
            from milenium.cli import main
            args = shlex.split(cmd)
            try:
                main(args, standalone_mode=False)
            except SystemExit:
                pass
            except Exception as e:
                console.print(f"[bold red]Ошибка:[/bold red] {e}")
        except KeyboardInterrupt:
            console.print("\n[bold red]Прервано.[/bold red]")
            break