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
    ("ПОИСК ЛЮДЕЙ", [
        ("user <ник>", "Maigret + Sherlock"),
        ("email_cmd <email>", "Holehe + VirusTotal"),
        ("phone_cmd <номер>", "Оператор, страна"),
        ("tg <username>", "Telethon: TG-аккаунт"),
        ("img <path>", "PicImageSearch"),
        ("social_cmd <ник>", "Соцсети по нику"),
    ]),
    ("СЕТЬ", [
        ("ip_cmd <IP>", "Shodan + Censys + VT + Abuse"),
        ("dom <домен>", "WHOIS, DNS, crt.sh"),
        ("url_cmd <URL>", "urlscan.io"),
        ("whois_rev <домен>", "Reverse WHOIS"),
        ("ssl_info <host>", "SSL-сертификат"),
        ("robots <домен>", "robots.txt"),
    ]),
    ("УТЕЧКИ", [
        ("pwned <пароль>", "Pwned Passwords"),
        ("leaks <email>", "HIBP утечки"),
        ("full --email E", "Агрегатор"),
        ("pwgen --name N", "Генератор паролей"),
    ]),
    ("ФАЙЛЫ", [
        ("exif <path>", "EXIF из фото"),
        ("eml <path>", "Заголовки письма"),
        ("wayback <url>", "Wayback Machine"),
    ]),
    ("БАЗА", [
        ("db_neon --stats", "Статистика NeonDB"),
        ("db_neon --target X", "Поиск по базе"),
        ("db_findings", "Найденные ссылки"),
        ("db_leaks", "Утечки"),
    ]),
    ("КОНФИГ", [
        ("config_cmd", "Показать конфиг"),
        ("config_cmd --key K --value V", "Задать ключ"),
    ]),
    ("СИСТЕМА", [
        ("help", "Список команд"),
        ("clear", "Очистить вывод"),
        ("exit / q", "Выход"),
    ]),
]

SESSION = {
    "start": datetime.now(),
    "queries": 0,
    "results": 0,
    "last": [],
    "current": None,
    "current_start": None,
}

OUTPUT_LOG = []
RESULT_LOG = []


def push_output(text):
    ts = datetime.now().strftime("%H:%M:%S")
    OUTPUT_LOG.append(f"[red]{ts}[/red] [white]{text}[/white]")
    if len(OUTPUT_LOG) > 200:
        OUTPUT_LOG.pop(0)


def push_result(text):
    RESULT_LOG.append(text)
    if len(RESULT_LOG) > 500:
        RESULT_LOG.pop(0)


def clear_result():
    RESULT_LOG.clear()


def log_result(text):
    ts = datetime.now().strftime("%H:%M:%S")
    SESSION["last"].append(f"[red]{ts}[/red] {text}")
    if len(SESSION["last"]) > 12:
        SESSION["last"].pop(0)


def build_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=7),
        Layout(name="body", size=18),
        Layout(name="process", size=8),
        Layout(name="result", size=14),
        Layout(name="input", size=3),
        Layout(name="footer", size=3),
    )
    layout["body"].split_row(
        Layout(name="left", ratio=3, minimum_size=55),
        Layout(name="center", ratio=2, minimum_size=35),
        Layout(name="right", ratio=2, minimum_size=35),
    )
    return layout


def render_header():
    logo_text = Text(LOGO, style="bold red")
    banner = Text.from_markup(
        "[bold white]MILENIUM[/bold white] [red]|[/red] [bold white]@VexxDev200[/bold white] "
        "[red]|[/red] [bold white]TG:[/bold white] [red]@milenium[/red] "
        "[red]|[/red] [green]● ONLINE[/green]"
    )
    return Panel(
        Align.center(logo_text + banner),
        border_style="red",
        title="[bold red]MILENIUM[/bold red]",
        subtitle="[red]v1.0.5[/red]",
    )


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
    return Panel(cols, title="[bold red]ВСЕ КОМАНДЫ[/bold red]", border_style="red")


def render_session():
    lines = []
    uptime = datetime.now() - SESSION["start"]
    mins, secs = divmod(int(uptime.total_seconds()), 60)
    lines.append(f"[white]Uptime:[/white]    [red]{mins:02d}:{secs:02d}[/red]")
    lines.append(f"[white]Запросов:[/white]  [red]{SESSION['queries']}[/red]")
    lines.append(f"[white]Найдено:[/white]   [red]{SESSION['results']}[/red]")

    if SESSION["current"]:
        elapsed = time.time() - SESSION["current_start"]
        lines.append("")
        lines.append(f"[bold yellow]▶ {SESSION['current']}[/bold yellow]")
        lines.append(f"[yellow]  идёт {elapsed:.1f}s...[/yellow]")

    lines.append("")
    lines.append("[bold red]━━ ПОСЛЕДНИЕ ━━[/bold red]")
    if SESSION["last"]:
        lines.extend(SESSION["last"][-8:])
    else:
        lines.append("[white]Пока ничего.[/white]")
    return Panel("\n".join(lines), title="[bold red]СЕССИЯ[/bold red]", border_style="red")


def render_status():
    from milenium.modules import neon_db, config

    cfg = config.all_keys()
    locked = config.locked_keys()
    lines = []
    lines.append("[bold red]━━ NEON DB ━━[/bold red]")
    db_url = cfg.get("DATABASE_URL", "")
    lines.append(f"[white]URL:[/white] [green]🔒 LOCKED[/green]" if db_url else "[red]NOT SET[/red]")
    try:
        s = neon_db.stats()
        lines.append(f"[white]Записей:[/white]  [red]{s['total']}[/red]")
        lines.append(f"[white]Findings:[/white] [red]{s['findings']}[/red]")
        lines.append(f"[white]Leaks:[/white]    [red]{s['leaks']}[/red]")
    except Exception as e:
        lines.append(f"[red]ERR: {str(e)[:60]}[/red]")

    lines.append("")
    lines.append("[bold red]━━ API КЛЮЧИ ━━[/bold red]")
    keys = [
        ("SHODAN", "SHODAN_API_KEY"),
        ("CENSYS", "CENSYS_TOKEN"),
        ("VTOTAL", "VIRUSTOTAL_API_KEY"),
        ("ABUSE", "ABUSEIPDB_KEY"),
        ("IPINFO", "IPINFO_TOKEN"),
        ("URLSCAN", "URLSCAN_API_KEY"),
        ("TG_ID", "TG_API_ID"),
        ("TG_HASH", "TG_API_HASH"),
        ("BOT_TOKEN", "TG_BOT_TOKEN"),
        ("SERPER", "SERPER_API_KEY"),
        ("HIBP", "HIBP_KEY"),
    ]
    for name, key in keys:
        ok = bool(cfg.get(key))
        is_locked = key in locked
        if is_locked:
            color = "yellow"
            mark = "🔒"
        elif ok:
            color = "green"
            mark = "✓"
        else:
            color = "red"
            mark = "✗"
        lines.append(f"[white]{name}[/white]  [{color}]{mark}[/{color}]")

    lines.append("")
    lines.append("[bold red]━━ МОДУЛИ ━━[/bold red]")
    for m in ["whois", "dns", "requests", "aiohttp", "rich"]:
        lines.append(f"[white]{m}[/white] [green]OK[/green]")
    return Panel("\n".join(lines), title="[bold red]СТАТУС[/bold red]", border_style="red")


def render_process():
    lines = ["[bold red]━━ ПРОЦЕСС ━━[/bold red]"]
    if OUTPUT_LOG:
        lines.extend(OUTPUT_LOG[-6:])
    else:
        lines.append("[white]Введи команду ниже.[/white]")
    return Panel("\n".join(lines), title="[bold red]ПРОЦЕСС[/bold red]", border_style="red")


def render_result():
    lines = ["[bold red]━━ РЕЗУЛЬТАТ ━━[/bold red]"]
    if RESULT_LOG:
        lines.extend(RESULT_LOG[-12:])
    else:
        lines.append("[white]Здесь появится результат команды.[/white]")
    return Panel("\n".join(lines), title="[bold red]РЕЗУЛЬТАТ[/bold red]", border_style="red")


def render_input():
    return Panel(
        "[bold red]milenium[/bold red] [white]@[/white] [red]VexxDev200[/red] [white]~[/white] "
        "[bold white]введи команду[/bold white]",
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
    layout["process"].update(render_process())
    layout["result"].update(render_result())
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
        clear_result()
        push_output("вывод очищен")
        return True
    return False


def _first_run_wizard():
    from milenium.modules import config
    console.clear()
    console.print(Panel(
        "[bold red]ПЕРВЫЙ ЗАПУСК — НАСТРОЙКА[/bold red]\n\n"
        f"Конфиг: [white]{config.config_path()}[/white]\n\n"
        "Введи ключи (Enter — пропустить). Потом можно менять через [red]config_cmd[/red].",
        border_style="red",
        title="[bold red]MILENIUM SETUP[/bold red]",
    ))
    keys = [
        ("SHODAN_API_KEY", "Shodan API key"),
        ("CENSYS_TOKEN", "Censys token"),
        ("VIRUSTOTAL_API_KEY", "VirusTotal API key"),
        ("ABUSEIPDB_KEY", "AbuseIPDB key"),
        ("IPINFO_TOKEN", "ipinfo.io token"),
        ("URLSCAN_API_KEY", "urlscan.io key"),
        ("TG_API_ID", "Telegram API ID"),
        ("TG_API_HASH", "Telegram API hash"),
        ("SERPER_API_KEY", "Serper.dev key"),
        ("HIBP_KEY", "HaveIBeenPwned key"),
    ]
    saved = {}
    for key, desc in keys:
        val = Prompt.ask(f"[red]{key}[/red] [white]({desc})[/white]", default="")
        if val.strip():
            saved[key] = val.strip()
    if saved:
        config.set_many(saved)
        console.print(f"[green]Сохранено {len(saved)} ключей.[/green]")
    else:
        console.print("[yellow]Ключи не заданы — можно позже через config_cmd.[/yellow]")
    time.sleep(1)
    console.clear()


def interactive():
    from milenium.modules import config

    if config.is_first_run():
        _first_run_wizard()

    config.apply_to_env()
    console.clear()
    set_progress_callback(push_output)
    push_output("сессия запущена")
    push_output("введи 'help' для подсказки")

    with Live(draw(), refresh_per_second=4) as live:
        while True:
            try:
                live.stop()
                cmd = Prompt.ask(
                    "[bold red]milenium[/bold red] [white]@[/white] "
                    "[red]VexxDev200[/red] [white]~[/white]"
                )
                live.start()

                if cmd.strip().lower() in ("exit", "quit", "q"):
                    break
                if not cmd.strip():
                    live.update(draw())
                    continue

                SESSION["queries"] += 1
                SESSION["current"] = cmd.strip()
                SESSION["current_start"] = time.time()
                push_output(f"▶ выполняю: {cmd}")
                clear_result()
                live.update(draw())

                if _handle_builtin(cmd):
                    SESSION["current"] = None
                    live.update(draw())
                    continue

                from milenium.cli import main
                t0 = time.time()
                args = shlex.split(cmd)
                buf = io.StringIO()
                try:
                    with contextlib.redirect_stdout(buf):
                        main(args, standalone_mode=False)
                    raw = buf.getvalue()
                    for line in raw.splitlines():
                        if line.strip():
                            push_result(line)
                            log_result(line[:80])
                            SESSION["results"] += 1
                except SystemExit:
                    pass
                except Exception as e:
                    push_result(f"[red]ошибка: {e}[/red]")

                elapsed = time.time() - t0
                push_output(f"✔ завершено за {elapsed:.1f}s")
                SESSION["current"] = None
                live.update(draw())

            except KeyboardInterrupt:
                break
    console.clear()