import sys
import shlex
import io
import contextlib
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

# Все команды с категориями
COMMANDS = {
    "ПОИСК ЛЮДЕЙ": [
        ("user <ник> [--permutations N] [--dorks]", "Глубокий поиск по нику + вариации + Google Dorks"),
        ("social_cmd <ник>", "Поиск соцсетей по нику"),
        ("email_check <email>", "SMTP + Gravatar + PGP + GitHub по email"),
        ("mail <email>", "MX, HIBP, Gravatar"),
        ("phone_cmd <номер>", "Оператор, страна, часовой пояс"),
        ("telegram <канал>", "Парсинг публичного Telegram-канала"),
    ],
    "УТЕЧКИ И ПАРОЛИ": [
        ("pwned <пароль>", "Проверка пароля в утечках (бесплатно)"),
        ("leaks <email>", "HIBP утечки"),
        ("pwgen [--name N] [--surname S] [--year Y] [--nick N]", "Генератор вероятных паролей"),
        ("full [--email E] [--username U] [--phone P] [--password PW]", "Агрегатор всех модулей"),
    ],
    "СЕТЬ И ДОМЕНЫ": [
        ("ip_cmd <IP>", "Гео, ASN, reverse DNS, Shodan, репутация"),
        ("dom <домен>", "WHOIS, DNS, subdomains, crt.sh"),
        ("whois_rev <домен>", "Reverse WHOIS"),
        ("ssl_info <host>", "SSL-сертификат: издатель, даты, SAN"),
        ("robots <домен>", "robots.txt + sitemap"),
        ("subdomains <домен>", "Перебор поддоменов"),
    ],
    "ФАЙЛЫ И МЕТАДАННЫЕ": [
        ("exif <path>", "EXIF/GPS из фото"),
        ("pdf_meta <path>", "Метаданные PDF"),
        ("eml <path>", "Анализ заголовков письма"),
        ("wayback <url>", "Wayback Machine"),
    ],
    "ИНТЕРФЕЙС": [
        ("tui", "Этот интерфейс"),
        ("exit / q", "Выход"),
    ],
}

SESSION = {
    "start": datetime.now(),
    "queries": 0,
    "results": 0,
    "last": [],
    "db_path": None,
    "db_loaded": False,
}

OUTPUT_LOG = []


def push_output(text):
    ts = datetime.now().strftime("%H:%M:%S")
    OUTPUT_LOG.append(f"[red]{ts}[/red] [white]{text}[/white]")
    if len(OUTPUT_LOG) > 50:
        OUTPUT_LOG.pop(0)


def log_result(text):
    ts = datetime.now().strftime("%H:%M:%S")
    SESSION["last"].append(f"[red]{ts}[/red] {text}")
    if len(SESSION["last"]) > 15:
        SESSION["last"].pop(0)


def build_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=9),
        Layout(name="body", ratio=3),
        Layout(name="output", size=12),
        Layout(name="input", size=3),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="left", ratio=2),
        Layout(name="center", ratio=2),
        Layout(name="right", ratio=1),
    )
    return layout


def render_header():
    logo = Text.from_markup(ASCII_LOGO)
    banner = Text.from_markup(BANNER)
    return Panel(Align.center(logo + banner), border_style="red", title="[bold red]MILENIUM[/bold red]", subtitle="[red]v0.5.2[/red]")


def render_commands():
    table = Table(show_header=True, box=None, padding=(0, 1), header_style="bold red")
    table.add_column("Команда", style="bold white")
    table.add_column("Описание", style="red")
    for category, cmds in COMMANDS.items():
        table.add_row(f"[bold red]━━ {category} ━━[/bold red]", "")
        for cmd, desc in cmds:
            table.add_row(f"[white]{cmd}[/white]", f"[red]{desc}[/red]")
    return Panel(table, title="[bold red]ВСЕ КОМАНДЫ[/bold red]", border_style="red")


def render_session():
    lines = []
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
        lines.append("[white]Пока ничего.[/white]")
    return Panel("\n".join(lines), title="[bold red]СЕССИЯ[/bold red]", border_style="red")


def render_status():
    lines = []
    lines.append("[bold red]МОДУЛИ:[/bold red]")
    for m in ["whois", "dns", "requests", "rich", "click", "phonenumbers", "bs4"]:
        lines.append(f"[white]{m}:[/white] [green]OK[/green]")
    lines.append("")
    lines.append("[bold red]API-КЛЮЧИ:[/bold red]")
    lines.append("[white]HIBP:[/white]        [red]NOT SET[/red]")
    lines.append("[white]DeHashed:[/white]    [red]NOT SET[/red]")
    lines.append("[white]LeakCheck:[/white]   [red]NOT SET[/red]")
    lines.append("[white]Serper:[/white]      [red]NOT SET[/red]")
    lines.append("[white]Shodan:[/white]      [red]NOT SET[/red]")
    return Panel("\n".join(lines), title="[bold red]СТАТУС[/bold red]", border_style="red")


def render_output():
    lines = ["[bold red]=== ПРОЦЕСС ===[/bold red]"]
    if OUTPUT_LOG:
        lines.extend(OUTPUT_LOG[-10:])
    else:
        lines.append("[white]Введи команду ниже.[/white]")
    return Panel("\n".join(lines), title="[bold red]ВЫВОД[/bold red]", border_style="red")


def render_input():
    return Panel(
        "[bold red]milenium[/bold red] [white]@[/white] [red]VexxDev200[/red] [white]~[/white] [bold white]введи команду[/bold white]",
        title="[bold red]ВВОД[/bold red]",
        border_style="red",
    )


def render_footer():
    return Panel(
        Align.center("[bold red]milenium[/bold red] [white]@[/white] [red]VexxDev200[/red]  [white]|[/white]  [green]SYSTEM READY[/green]  [white]|[/white]  [red]ESC/Ctrl+C для выхода[/red]"),
        border_style="red",
    )


def draw():
    layout = build_layout()
    layout["header"].update(render_header())
    layout["left"].update(render_commands())
    layout["center"].update(render_session())
    layout["right"].update(render_status())
    layout["output"].update(render_output())
    layout["input"].update(render_input())
    layout["footer"].update(render_footer())
    return layout


def interactive():
    console.clear()
    push_output("сессия запущена")
    push_output("введи 'help' для списка команд")
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