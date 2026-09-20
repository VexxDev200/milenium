import os
import asyncio
import subprocess
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from milenium.modules import config

BOT_TOKEN = config.get("TG_BOT_TOKEN", "8787278495:AAHhpSWVI4b88hYBZlfd_IvHkq2GW_YNRDQ")
ALLOWED_USERS = config.get("TG_ALLOWED_USERS", "5496853233")  # через запятую, пусто = все

bot = Bot(token=BOT_TOKEN) if BOT_TOKEN else None
dp = Dispatcher()


def _allowed(user_id: int) -> bool:
    allowed = config.get("TG_ALLOWED_USERS", "")
    if not allowed:
        return True
    return str(user_id) in [x.strip() for x in allowed.split(",")]


def _run_cli(args: list) -> str:
    """Запускает milenium CLI и возвращает stdout."""
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "milenium.cli"] + args,
            capture_output=True, text=True, timeout=180
        )
        out = proc.stdout.strip() or proc.stderr.strip()
        return out[:4000] or "(пусто)"
    except subprocess.TimeoutExpired:
        return "⏱ таймаут 180с"
    except Exception as e:
        return f"ошибка: {e}"


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if not _allowed(message.from_user.id):
        return
    await message.answer(
        "🤖 milenium bot\n\n"
        "Команды:\n"
        "/ip <IP> — Shodan + Censys + VT + Abuse\n"
        "/user <ник> — Maigret + Sherlock\n"
        "/email <email> — Holehe + VT\n"
        "/dom <домен> — WHOIS + DNS + crt.sh\n"
        "/url <URL> — urlscan.io\n"
        "/tg <username> — Telethon\n"
        "/pwned <пароль> — Pwned Passwords\n"
        "/db — статистика NeonDB\n"
        "/help — эта справка"
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await cmd_start(message)


@dp.message(Command("ip"))
async def cmd_ip(message: types.Message):
    if not _allowed(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("использование: /ip 8.8.8.8")
        return
    await message.answer(f"⏳ ip_cmd {parts[1]}")
    out = await asyncio.to_thread(_run_cli, ["ip_cmd", parts[1]])
    await message.answer(f"```\n{out}\n```", parse_mode="Markdown")


@dp.message(Command("user"))
async def cmd_user(message: types.Message):
    if not _allowed(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("использование: /user <ник>")
        return
    await message.answer(f"⏳ user {parts[1]}")
    out = await asyncio.to_thread(_run_cli, ["user", parts[1]])
    await message.answer(f"```\n{out}\n```", parse_mode="Markdown")


@dp.message(Command("email"))
async def cmd_email(message: types.Message):
    if not _allowed(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("использование: /email test@example.com")
        return
    await message.answer(f"⏳ email_cmd {parts[1]}")
    out = await asyncio.to_thread(_run_cli, ["email_cmd", parts[1]])
    await message.answer(f"```\n{out}\n```", parse_mode="Markdown")


@dp.message(Command("dom"))
async def cmd_dom(message: types.Message):
    if not _allowed(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("использование: /dom example.com")
        return
    await message.answer(f"⏳ dom {parts[1]}")
    out = await asyncio.to_thread(_run_cli, ["dom", parts[1]])
    await message.answer(f"```\n{out}\n```", parse_mode="Markdown")


@dp.message(Command("url"))
async def cmd_url(message: types.Message):
    if not _allowed(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("использование: /url https://example.com")
        return
    await message.answer(f"⏳ url_cmd {parts[1]}")
    out = await asyncio.to_thread(_run_cli, ["url_cmd", parts[1]])
    await message.answer(f"```\n{out}\n```", parse_mode="Markdown")


@dp.message(Command("tg"))
async def cmd_tg(message: types.Message):
    if not _allowed(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("использование: /tg durov")
        return
    await message.answer(f"⏳ tg {parts[1]}")
    out = await asyncio.to_thread(_run_cli, ["tg", parts[1]])
    await message.answer(f"```\n{out}\n```", parse_mode="Markdown")


@dp.message(Command("pwned"))
async def cmd_pwned(message: types.Message):
    if not _allowed(message.from_user.id):
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("использование: /pwned password123")
        return
    out = await asyncio.to_thread(_run_cli, ["pwned", parts[1]])
    await message.answer(f"```\n{out}\n```", parse_mode="Markdown")


@dp.message(Command("db"))
async def cmd_db(message: types.Message):
    if not _allowed(message.from_user.id):
        return
    out = await asyncio.to_thread(_run_cli, ["db_neon", "--stats"])
    await message.answer(f"```\n{out}\n```", parse_mode="Markdown")


async def run_bot():
    if not BOT_TOKEN:
        print("TG_BOT_TOKEN не задан в конфиге")
        return
    print("бот запущен")
    await dp.start_polling(bot)


def main():
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()