import sys
import time
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.live import Live
from rich.prompt import Prompt

console = Console()

# ASCII-арт "M" в красном стиле
ASCII_LOGO = r"""
[bold red]
 ███╗   ███╗ ██╗ ██╗     ███████╗ ███╗   ██╗ ██╗ ██╗   ██╗ ███╗   ███╗
 ████╗ ████║ ██║ ██║     ██╔════╝ ████╗  ██║ ██║ ██║   ██║ ████╗ ████║
 ██╔████╔██║ ██║ ██║     █████╗   ██╔██╗ ██║ ██║ ██║   ██║ ██╔████╔██║
 ██║╚██╔╝██║ ██║ ██║     ██╔══╝   ██║╚██╗██║ ██║ ██║   ██║ ██║╚██╔╝██║
 ██║ ╚═╝ ██║ ██║ ███████╗ ███████╗ ██║ ╚████║ ██║ ╚██████╔╝ ██║ ╚═╝ ██║
 ╚═╝     ╚═╝ ╚═╝ ╚══════╝ ╚══════╝ ╚═╝  ╚═══╝ ╚═╝  ╚═════╝  ╚═╝     ╚═╝
[/bold red]
"""

BANNER = """
[bold red]╔══════════════════════════════════════════════════════════════════════════╗
║  [bold white]MILENIUM C2[/bold white]  [red]|[/red]  [bold white]FULLY DESIGNED BY[/bold white] [red]@VexxDev200[/red]              ║
║  [red]|[/red]  [bold white]JOIN OUR CHANNELS[/bold white]  [red]|[/red]  [bold white]TG:[/bold white] [red]@milenium[/red]                       ║
║  [red]|[/red]  [bold white]DC:[/bold white] [red]milenium[/red]  [red]|[/red]  [bold white]STATUS:[/bold white] [green]● ONLINE[/green]                      ║
╚══════════════════════════════════════════════════════════════════════════╝[/bold red]
"""

# Меню (только интерфейс, никаких реальных функций)
MENU_ITEMS = [
    ("1", "user <ник>", "Поиск по соцсетям + вариации"),
    ("2", "mail <email>", "MX, HIBP, Gravatar"),
    ("3", "phone_cmd <номер>", "Оператор, страна"),
    ("4", "ip_cmd <IP>", "Гео, ASN, Shodan"),
    ("5", "dom <домен>", "WHOIS, DNS, crt.sh"),
    ("6", "leaks <email>", "Утечки HIBP"),
    ("7", "social_cmd <ник>", "Соцсети"),
    ("8", "pwned <пароль>", "Проверка пароля"),
    ("9", "telegram <канал>", "Парсинг TG"),
    ("A", "full --email ...", "Агрегатор"),
    ("T", "tui", "Этот интерфейс"),
    ("Q", "exit", "Выход"),
]

def build_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=10),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="center", ratio=2),
        Layout(name="right", ratio=1),
    )
    return layout

def render_header():
    logo = Text.from_markup(ASCII_LOGO)
    banner = Text.from_markup(BANNER)
    return Panel(
        Align.center(logo + banner),
        border_style="red",
        title="[bold red]MILENIUM[/bold red]",
        subtitle="[red]v0.4.0[/red]",
    )

def render_left():
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Key", style="bold red")
    table.add_column("Cmd", style="bold white")
    for key, cmd, _ in MENU_ITEMS:
        table.add_row(f"[{key}]", cmd)
    return Panel(
        table,
        title="[bold red]МЕНЮ[/bold red]",
        border_style="red",
        subtitle="[red]выбери команду[/red]",
    )

def render_center():
    lines = []
    lines.append("[bold red]=== LAYER 7 ===[/bold red]")
    for i in range(1, 8):
        lines.append(f"[red]{i}[/red]  [white]module_{i}[/white]..............[red]url[/red] <port> <time>")
    lines.append("")
    lines.append("[bold red]=== UDP ===[/bold red]")
    for i in range(1, 8):
        lines.append(f"[red]{i}[/red]  [white]udp_{i}[/white].................[red]ip[/red] <port> <time>")
    lines.append("")
    lines.append("[bold red]=== TCP ===[/bold red]")
    for i in range(1, 8):
        lines.append(f"[red]{i}[/red]  [white]tcp_{i}[/white].................[red]ip[/red] <port> <time>")
    lines.append("")
    lines.append("[bold red]=== BOTNET ===[/bold red]")
    for i in range(1, 8):
        lines.append(f"[red]{i}[/red]  [white]bot_{i}[/white].................[red]ip[/red] <port> <time>")
    return Panel(
        "\n".join(lines),
        title="[bold red]МОДУЛИ[/bold red]",
        border_style="red",
    )

def render_right():
    lines = []
    lines.append("[bold red]Roles Needed:[/bold red]")
    lines.append("")
    lines.append("[white]Requirements:[/white] [red](VIP)[/red]")
    lines.append("[white]Requirements:[/white] [red](VIP)[/red]")
    lines.append("[white]Requirements:[/white] [red](VIP)[/red]")
    lines.append("[white]Requirements:[/white] [red](BOTNET)[/red]")
    lines.append("[white]Requirements:[/white] [red](HOLDER)[/red]")
    lines.append("")
    lines.append("[bold red]Network Status:[/bold red]")
    lines.append("[green]● ONLINE[/green]")
    lines.append("[green]● ONLINE[/green]")
    lines.append("[green]● ONLINE[/green]")
    return Panel(
        "\n".join(lines),
        title="[bold red]СТАТУС[/bold red]",
        border_style="red",
    )

def render_footer():
    return Panel(
        Align.center("[bold red]milenium[/bold red] [white]@[/white] [red]VexxDev200[/red]  [white]|[/white]  [green]SYSTEM READY[/green]"),
        border_style="red",
    )

def draw():
    layout = build_layout()
    layout["header"].update(render_header())
    layout["left"].update(render_left())
    layout["center"].update(render_center())
    layout["right"].update(render_right())
    layout["footer"].update(render_footer())
    return layout

def interactive():
    console.clear()
    with Live(draw(), refresh_per_second=4, screen=True) as live:
        while True:
            try:
                cmd = Prompt.ask("[bold red]milenium[/bold red] [white]@[/white] [red]VexxDev200[/red] [white]~[/white]")
                if cmd.strip().lower() in ("exit", "quit", "q"):
                    break
                if not cmd.strip():
                    continue
                # Выполняем реальную CLI-команду
                import shlex
                from milenium.cli import main
                args = shlex.split(cmd)
                try:
                    main(args, standalone_mode=False)
                except SystemExit:
                    pass
                except Exception as e:
                    console.print(f"[bold red]Ошибка:[/bold red] {e}")
                # Обновляем Live
                live.update(draw())
            except KeyboardInterrupt:
                break
    console.clear()