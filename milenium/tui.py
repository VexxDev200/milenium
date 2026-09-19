import sys
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.align import Align
from rich.live import Live
from rich.prompt import Prompt

console = Console()

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
║  [bold white]MILENIUM[/bold white]  [red]|[/red]  [bold white]DESIGNED BY[/bold white] [red]@VexxDev200[/red]                     ║
║  [red]|[/red]  [bold white]TG:[/bold white] [red]@milenium[/red]  [red]|[/red]  [bold white]DC:[/bold white] [red]milenium[/red]  [red]|[/red]  [bold white]STATUS:[/bold white] [green]● ONLINE[/green]      ║
╚══════════════════════════════════════════════════════════════════════════╝[/bold red]
"""

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

SESSION = {
    "start": datetime.now(),
    "queries": 0,
    "results": 0,
    "last": [],
    "db_path": None,
    "db_loaded": False,
}

OUTPUT_LOG = []  # буфер вывода последних строк

def push_output(text):
    ts = datetime.now().strftime("%H:%M:%S")
    OUTPUT_LOG.append(f"[red]{ts}[/red] [white]{text}[/white]")
    if len(OUTPUT_LOG) > 20:
        OUTPUT_LOG.pop(0)


def clear_output():
    OUTPUT_LOG.clear()

def render_output():
    lines = []
    lines.append("[bold red]=== ВЫВОД КОМАНДЫ ===[/bold red]")
    if OUTPUT_LOG:
        lines.extend(OUTPUT_LOG[-10:])
    else:
        lines.append("[white]Пока ничего. Введи команду ниже.[/white]")
    return Panel(
        "\n".join(lines),
        title="[bold red]ПРОЦЕСС[/bold red]",
        border_style="red",
    )


def render_input():
    return Panel(
        "[bold red]milenium[/bold red] [white]@[/white] [red]VexxDev200[/red] [white]~[/white] [bold white]введи команду ниже[/bold white]",
        title="[bold red]ВВОД[/bold red]",
        border_style="red",
    )


def log_result(text):
    ts = datetime.now().strftime("%H:%M:%S")
    SESSION["last"].append(f"[red]{ts}[/red] {text}")
    if len(SESSION["last"]) > 15:
        SESSION["last"].pop(0)


def build_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=10),
        Layout(name="body", ratio=2),
        Layout(name="output", size=12),
        Layout(name="input", size=3),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="center", ratio=2),
        Layout(name="right", ratio=1),
    )
    return layout


def render_input():
    return Panel(
        "[bold red]milenium[/bold red] [white]@[/white] [red]VexxDev200[/red] [white]~[/white] [bold white]введи команду ниже[/bold white]",
        title="[bold red]ВВОД[/bold red]",
        border_style="red",
    )


def render_header():
    logo = Text.from_markup(ASCII_LOGO)
    banner = Text.from_markup(BANNER)
    return Panel(
        Align.center(logo + banner),
        border_style="red",
        title="[bold red]MILENIUM[/bold red]",
        subtitle="[red]v0.4.2[/red]",
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
    lines.append("[bold red]=== СТАТИСТИКА СЕССИИ ===[/bold red]")
    uptime = datetime.now() - SESSION["start"]
    mins, secs = divmod(int(uptime.total_seconds()), 60)
    lines.append(f"[white]Uptime:[/white]      [red]{mins:02d}:{secs:02d}[/red]")
    lines.append(f"[white]Запросов:[/white]    [red]{SESSION['queries']}[/red]")
    lines.append(f"[white]Найдено:[/white]     [red]{SESSION['results']}[/red]")
    lines.append(f"[white]База:[/white]        [red]{'LOADED' if SESSION['db_loaded'] else 'NOT LOADED'}[/red]")
    lines.append("")
    lines.append("[bold red]=== ПОСЛЕДНИЕ РЕЗУЛЬТАТЫ ===[/bold red]")
    if SESSION["last"]:
        lines.extend(SESSION["last"])
    else:
        lines.append("[white]Пока ничего. Запусти команду.[/white]")
    return Panel(
        "\n".join(lines),
        title="[bold red]СЕССИЯ[/bold red]",
        border_style="red",
    )


def render_right():
    lines = []
    lines.append("[bold red]СОСТОЯНИЕ МОДУЛЕЙ:[/bold red]")
    lines.append("")
    lines.append("[white]whois:[/white]       [green]OK[/green]")
    lines.append("[white]dns:[/white]         [green]OK[/green]")
    lines.append("[white]requests:[/white]    [green]OK[/green]")
    lines.append("[white]rich:[/white]        [green]OK[/green]")
    lines.append("[white]click:[/white]       [green]OK[/green]")
    lines.append("[white]phonenumbers:[/white][green]OK[/green]")
    lines.append("[white]bs4:[/white]         [green]OK[/green]")
    lines.append("")
    lines.append("[bold red]API-КЛЮЧИ:[/bold red]")
    lines.append("[white]HIBP:[/white]        [red]NOT SET[/red]")
    lines.append("[white]DeHashed:[/white]    [red]NOT SET[/red]")
    lines.append("[white]LeakCheck:[/white]   [red]NOT SET[/red]")
    lines.append("[white]Serper:[/white]      [red]NOT SET[/red]")
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
    layout["output"].update(render_output())
    layout["input"].update(render_input())
    layout["footer"].update(render_footer())
    return layout


def interactive():
    console.clear()
    push_output("сессия запущена")
    with Live(draw(), refresh_per_second=4) as live:
        while True:
            try:
                live.stop()
                cmd = Prompt.ask("[bold red]milenium[/bold red] [white]@[/white] [red]VexxDev200[/red] [white]~[/white]")
                live.start()

                if cmd.strip().lower() in ("exit", "quit", "q"):
                    break
                if not cmd.strip():
                    live.update(draw())
                    continue

                SESSION["queries"] += 1
                push_output(f"выполняю: {cmd}")

                import shlex
                import io
                import contextlib
                from milenium.cli import main

                args = shlex.split(cmd)
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf):
                        main(args, standalone_mode=False)
                    for line in buf.getvalue().splitlines():
                        if line.strip():
                            push_output(line)
                except SystemExit:
                    pass
                except Exception as e:
                    push_output(f"[red]ошибка: {e}[/red]")
                live.update(draw())
            except KeyboardInterrupt:
                break
    console.clear()