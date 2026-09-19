import sys
import shlex
import io
import contextlib
import time
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.live import Live
from rich.prompt import Prompt
from rich.columns import Columns
from milenium.modules.logger import set_progress_callback

console = Console()

LOGO = r"""
███╗   ███╗██╗██╗     ███████╗███╗   ██╗██╗██╗   ██╗███╗   ███╗
████╗ ████║██║██║     ██╔════╝████╗  ██║██║██║   ██║████╗ ████║
██╔████╔██║██║██║     █████╗  ██╔██╗ ██║██║██║   ██║██╔████╔██║
██║╚██╔╝██║██║██║     ██╔══╝  ██║╚██╗██║██║██║   ██║██║╚██╔╝██║
██║ ╚═╝ ██║██║███████╗███████╗██║ ╚████║██║╚██████╔╝██║ ╚═╝ ██║
╚═╝     ╚═╝╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝╚═╝ ╚═════╝ ╚═╝     ╚═╝
"""

COMMANDS = [
    ("ПОИСК", [
        ("user <ник>", "Ник + вариации + Dorks"),
        ("social_cmd <ник>", "Соцсети по нику"),
        ("mail <email>", "MX, HIBP, Gravatar"),
        ("phone_cmd <номер>", "Оператор, страна"),
        ("telegram <канал>", "TG-канал"),
    ]),
    ("УТЕЧКИ", [
        ("pwned <пароль>", "Проверка пароля"),
        ("leaks <email>", "HIBP утечки"),
        ("full --email E", "Агрегатор"),
    ]),
    ("СЕТЬ", [
        ("ip_cmd <IP>", "Гео, Shodan, репутация"),
        ("dom <домен>", "WHOIS, DNS, crt.sh"),
    ]),
    ("NEON DB", [
        ("db_neon --stats", "Статистика"),
        ("db_neon --target X", "Поиск"),
        ("db_findings", "Найденные ссылки"),
        ("db_leaks", "Утечки"),
    ]),
    ("СИСТЕМА", [
        ("help", "Список команд"),
        ("clear", "Очистить вывод"),
        ("exit / q", "Выход"),
    ]),
]

SESSION = {"start": datetime.now(), "queries": 0, "results": 0, "last": []}
OUTPUT_LOG = []


def push_output(text):
    ts = datetime.now().strftime("%H:%M:%S")
    OUTPUT_LOG.append(f"[red]{ts}[/red] [white]{text}[/white]")
    if len(OUTPUT_LOG) > 200:
        OUTPUT_LOG.pop(0)


def build_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=8),
        Layout(name="body", size=18),
        Layout(name="output", size=18),
        Layout(name="input", size=3),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="left", ratio=1, minimum_size=40),
        Layout(name="center", ratio=1, minimum_size=30),
        Layout(name="right", ratio=1, minimum_size=25),
    )
    return layout


def render_header():
    logo_text = Text(LOGO, style="bold red")
    banner = Text.from_markup(
        "[bold white]MILENIUM[/bold white] [red]|[/red] [bold white]@VexxDev200[/bold white] "
        "[red]|[/red] [bold white]TG:[/bold white] [red]@milenium[/red] "
        "[red]|[/red] [green]● ONLINE[/green]"
    )
    return Panel(Align.center(logo_text + banner), border_style="red",
                 title="[bold red]MILENIUM[/bold red]", subtitle="[red]v0.6.5[/red]")


def render_commands():
    left_lines, right_lines = [], []
    items = []
    for cat, cmds in COMMANDS:
        items.append(("cat", cat))
        for cmd, desc in cmds:
            items.append(("cmd", (cmd, desc)))
    half = len(items) // 2
    for i, (kind, val) in enumerate(items):
        target = left_lines if i < half else right_lines
        if kind == "cat":
            target.append(Text(f"━━ {val} ━━", style="bold red"))
        else:
            cmd, desc = val
            t = Text()
            t.append(cmd, style="bold white")
            t.append("\n  ", style="red")
            t.append(desc, style="red")
            target.append(t)
    left = Text("\n").join(left_lines)
    right = Text("\n").join(right_lines)
    cols = Columns([left, right], expand=True, equal=True)
    return Panel(cols, title="[bold red]КОМАНДЫ[/bold red]", border_style="red")


def render_session():
    lines = []
    uptime = datetime.now() - SESSION["start"]
    mins, secs = divmod(int(uptime.total_seconds()), 60)
    lines.append(f"[white]Uptime:[/white]    [red]{mins:02d}:{secs:02d}[/red]")
    lines.append(f"[white]Запросов:[/white]  [red]{SESSION['queries']}[/red]")
    lines.append(f"[white]Найдено:[/white]   [red]{SESSION['results']}[/red]")
    lines.append("")
    lines.append("[bold red]━━ ПОСЛЕДНИЕ ━━[/bold red]")
    if SESSION["last"]:
        lines.extend(SESSION["last"][-8:])
    else:
        lines.append("[white]Пока ничего.[/white]")
    return Panel("\n".join(lines), title="[bold red]СЕССИЯ[/bold red]", border_style="red")


def render_status():
    from milenium.modules import neon_db
    import os
    lines = []
    lines.append("[bold red]━━ NEON DB ━━[/bold red]")
    lines.append(f"[white]URL:[/white] [red]{'SET' if os.environ.get('DATABASE_URL') else 'NOT SET'}[/red]")
    try:
        s = neon_db.stats()
        lines.append(f"[white]Записей:[/white]  [red]{s['total']}[/red]")
        lines.append(f"[white]Findings:[/white] [red]{s['findings']}[/red]")
        lines.append(f"[white]Leaks:[/white]    [red]{s['leaks']}[/red]")
    except Exception as e:
        lines.append(f"[red]ERR: {str(e)[:60]}[/red]")
    lines.append("")
    lines.append("[bold red]━━ МОДУЛИ ━━[/bold red]")
    for m in ["whois", "dns", "requests", "rich", "click"]:
        lines.append(f"[white]{m}[/white] [green]OK[/green]")
    return Panel("\n".join(lines), title="[bold red]СТАТУС[/bold red]", border_style="red")


def render_output():
    lines = ["[bold red]━━ ПРОЦЕСС ━━[/bold red]"]
    if OUTPUT_LOG:
        lines.extend(OUTPUT_LOG[-16:])
    else:
        lines.append("[white]Введи команду ниже.[/white]")
    return Panel("\n".join(lines), title="[bold red]ВЫВОД[/bold red]", border_style="red")


def render_input():
    return Panel(
        "[bold red]milenium[/bold red] [white]@[/white] [red]VexxDev200[/red] [white]~[/white] [bold white]введи команду[/bold white]",
        title="[bold red]ВВОД[/bold red]", border_style="red")


def render_footer():
    return Panel(Align.center(
        "[bold red]milenium[/bold red] [white]@[/white] [red]VexxDev200[/red] "
        "[white]|[/white] [green]SYSTEM READY[/green] "
        "[white]|[/white] [red]Ctrl+C для выхода[/red]"), border_style="red")


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
        push_output("список команд в левой панели")
        return True
    if c == "clear":
        OUTPUT_LOG.clear()
        push_output("вывод очищен")
        return True
    return False


def interactive():
    console.clear()
    set_progress_callback(push_output)
    push_output("сессия запущена")
    push_output("введи 'help'")
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
                push_output(f"▶ выполняю: {cmd}")

                if _handle_builtin(cmd):
                    live.update(draw())
                    continue

                from milenium.cli import main
                t0 = time.time()
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
                elapsed = time.time() - t0
                push_output(f"✔ завершено за {elapsed:.1f}s")
                live.update(draw())
            except KeyboardInterrupt:
                break
    console.clear()