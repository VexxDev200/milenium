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

LOGO = r"""
███╗   ███╗██╗██╗     ███████╗███╗   ██╗██╗██╗   ██╗███╗   ███╗
████╗ ████║██║██║     ██╔════╝████╗  ██║██║██║   ██║████╗ ████║
██╔████╔██║██║██║     █████╗  ██╔██╗ ██║██║██║   ██║██╔████╔██║
██║╚██╔╝██║██║██║     ██╔══╝  ██║╚██╗██║██║██║   ██║██║╚██╔╝██║
██║ ╚═╝ ██║██║███████╗███████╗██║ ╚████║██║╚██████╔╝██║ ╚═╝ ██║
╚═╝     ╚═╝╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝     ╚═╝
"""

COMMANDS = {
    "ПОИСК ЛЮДЕЙ": [
        ("user <ник>", "Поиск по соцсетям + вариации + Dorks"),
        ("social_cmd <ник>", "Поиск соцсетей по нику"),
        ("email_check <email>", "SMTP + Gravatar + PGP + GitHub"),
        ("mail <email>", "MX, HIBP, Gravatar"),
        ("phone_cmd <номер>", "Оператор, страна, часовой пояс"),
        ("telegram <канал>", "Парсинг публичного TG-канала"),
    ],
    "УТЕЧКИ И ПАРОЛИ": [
        ("pwned <пароль>", "Проверка пароля в утечках"),
        ("leaks <email>", "HIBP утечки"),
        ("pwgen --name N --year Y", "Генератор паролей"),
        ("full --email E --username U", "Агрегатор всех модулей"),
    ],
    "СЕТЬ И ДОМЕНЫ": [
        ("ip_cmd <IP>", "Гео, ASN, Shodan, репутация"),
        ("dom <домен>", "WHOIS, DNS, crt.sh"),
        ("whois_rev <домен>", "Reverse WHOIS"),
        ("ssl_info <host>", "SSL-сертификат"),
        ("robots <домен>", "robots.txt + sitemap"),
    ],
    "ФАЙЛЫ": [
        ("exif <path>", "EXIF/GPS из фото"),
        ("eml <path>", "Заголовки письма"),
        ("wayback <url>", "Wayback Machine"),
    ],
    "ИНТЕРФЕЙС": [
        ("help", "Показать все команды"),
        ("clear", "Очистить вывод"),
        ("exit / q", "Выход"),
    ],
}

SESSION = {
    "start": datetime.now(),
    "queries": 0,
    "results": 0,
    "last": [],
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
    if len(SESSION["last"]) > 10:
        SESSION["last"].pop(0)


def build_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=9),
        Layout(name="body", ratio=2),
        Layout(name="output", size=12),
        Layout(name="input", size=3),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="left", ratio=3),
        Layout(name="center", ratio=2),
        Layout(name="right", ratio=1),
    )
    return layout


def render_header():
    logo_text = Text(LOGO, style="bold red")
    banner = Text.from_markup(
        "[bold white]MILENIUM[/bold white] [red]|[/red] [bold white]@VexxDev200[/bold white] "
        "[red]|[/red] [bold white]TG:[/bold white] [red]@milenium[/red] "
        "[red]|[/red] [bold white]STATUS:[/bold white] [green]● ONLINE[/green]"
    )
    return Panel(
        Align.center(logo_text + banner),
        border_style="red",
        title="[bold red]MILENIUM[/bold red]",
        subtitle="[red]v0.5.3[/red]",
    )


def render_commands():
    table = Table(show_header=True, box=None, padding=(0, 1), header_style="bold red", expand=True)
    table.add_column("Команда", style="bold white", no_wrap=False)
    table.add_column("Описание", style="red", no_wrap=False)
    for category, cmds in COMMANDS.items():
        table.add_row(f"[bold red]━━ {category} ━━[/bold red]", "")
        for cmd, desc in cmds:
            table.add_row(cmd, desc)
    return Panel(table, title="[bold red]ВСЕ КОМАНДЫ[/bold red]", border_style="red")


def render_session():
    lines = []
    uptime = datetime.now() - SESSION["start"]
    mins, secs = divmod(int(uptime.total_seconds()), 60)
    lines.append(f"[white]Uptime:[/white]    [red]{mins:02d}:{secs:02d}[/red]")
    lines.append(f"[white]Запросов:[/white]  [red]{SESSION['queries']}[/red]")
    lines.append(f"[white]Найдено:[/white]   [red]{SESSION['results']}[/red]")
    lines.append(f"[white]База:[/white]      [red]{'LOADED' if SESSION['db_loaded'] else 'NOT LOADED'}[/red]")
    lines.append("")
    lines.append("[bold red]━━ ПОСЛЕДНИЕ ━━[/bold red]")
    if SESSION["last"]:
        lines.extend(SESSION["last"])
    else:
        lines.append("[white]Пока ничего.[/white]")
    return Panel("\n".join(lines), title="[bold red]СЕССИЯ[/bold red]", border_style="red")


def render_status():
    lines = []
    lines.append("[bold red]━━ МОДУЛИ ━━[/bold red]")
    for m in ["whois", "dns", "requests", "rich", "click"]:
        lines.append(f"[white]{m}[/white] [green]OK[/green]")
    lines.append("")
    lines.append("[bold red]━━ API ━━[/bold red]")
    for k in ["HIBP", "DeHashed", "LeakCheck", "Serper", "Shodan"]:
        lines.append(f"[white]{k}[/white] [red]NO[/red]")
    return Panel("\n".join(lines), title="[bold red]СТАТУС[/bold red]", border_style="red")


def render_output():
    lines = ["[bold red]━━ ПРОЦЕСС ━━[/bold red]"]
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
        Align.center(
            "[bold red]milenium[/bold red] [white]@[/white] [red]VexxDev200[/red] "
            "[white]|[/white] [green]SYSTEM READY[/green] "
            "[white]|[/white] [red]Ctrl+C для выхода[/red]"
        ),
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


def _handle_builtin(cmd):
    c = cmd.strip().lower()
    if c == "help":
        push_output("список команд — в левой панели")
        return True
    if c == "clear":
        OUTPUT_LOG.clear()
        push_output("вывод очищен")
        return True
    return False


def interactive():
    console.clear()
    push_output("сессия запущена")
    push_output("введи 'help' для подсказки")
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

                if _handle_builtin(cmd):
                    live.update(draw())
                    continue

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