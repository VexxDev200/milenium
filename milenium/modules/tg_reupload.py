import json
import asyncio
from pathlib import Path
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.tl.types import ChatInviteAlready, PeerChannel
from telethon.errors import UserAlreadyParticipantError, InviteHashExpiredError, FloodWaitError
from milenium.modules import config, logger


DEFAULT_SESSION = "milenium_tg_grab"
ARCHIVE_EXTS = {".csv", ".db", ".sqlite", ".sqlite3", ".json", ".txt", ".zip", ".rar", ".7z", ".tar", ".gz"}


def _parse_link(link: str):
    import re
    link = link.strip()
    if not link:
        return None, None
    m = re.search(r"(?:t\.me/\+|^\+)([A-Za-z0-9_-]{10,})", link)
    if m:
        return "invite", m.group(1)
    m = re.search(r"t\.me/([A-Za-z0-9_]{5,})", link)
    if m:
        return "public", m.group(1)
    if re.match(r"^@([A-Za-z0-9_]{5,})$", link):
        return "public", link[1:]
    return None, None


def load_accounts(accounts_file="data/tg_accounts.json"):
    import csv
    from pathlib import Path
    if accounts_file and Path(accounts_file).exists():
        path = Path(accounts_file)
        if path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and "accounts" in data:
                return data["accounts"]
            return data if isinstance(data, list) else []
        elif path.suffix.lower() == ".csv":
            accounts = []
            with open(path, "r", encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    accounts.append(dict(row))
            return accounts
    return [{
        "api_id": config.get("TG_API_ID", ""),
        "api_hash": config.get("TG_API_HASH", ""),
        "session": DEFAULT_SESSION,
    }]


async def _resolve_target(client, target, cache):
    pid = cache.get("peer_id")
    if pid:
        try:
            return await client.get_entity(PeerChannel(pid))
        except Exception:
            pass
    try:
        entity = await client.get_entity(target)
        if hasattr(entity, "id"):
            cache["peer_id"] = entity.id
        return entity
    except Exception as e:
        logger.progress(f"TG: get_entity target не сработал: {e}")
    kind, value = _parse_link(target)
    if kind == "invite":
        try:
            res = await client(CheckChatInviteRequest(value))
            if isinstance(res, ChatInviteAlready):
                cache["peer_id"] = res.chat.id
                return res.chat
        except Exception:
            pass
        try:
            updates = await client(ImportChatInviteRequest(value))
            return updates.chats[0] if updates.chats else None
        except UserAlreadyParticipantError:
            res = await client(CheckChatInviteRequest(value))
            return res.chat if isinstance(res, ChatInviteAlready) else None
        except InviteHashExpiredError:
            return None
    return None


async def _send_file(client, target_entity, local_path, target_cache):
    try:
        await client.send_file(target_entity, local_path, caption=Path(local_path).name)
        logger.progress(f"TG UPLOAD: отправлен {Path(local_path).name}")
        return True
    except FloodWaitError as e:
        logger.progress(f"TG UPLOAD: флуд, жду {e.seconds}s")
        await asyncio.sleep(e.seconds)
        return await _send_file(client, target_entity, local_path, target_cache)
    except Exception as e:
        logger.progress(f"TG UPLOAD: ошибка {Path(local_path).name}: {e}")
        return False


def _is_target_file(path: Path):
    ext = path.suffix.lower()
    if ext in ARCHIVE_EXTS:
        return True
    return False


async def reupload_local(local_dir="data/tg_dumps", accounts_file="data/tg_accounts.json", target="https://t.me/+pQduDv2K9gE2MTMy", delete_after=True):
    local_dir = Path(local_dir)
    if not local_dir.exists():
        return {"error": f"Folder not found: {local_dir}"}

    accounts = load_accounts(accounts_file)
    if not accounts:
        return {"error": "no accounts"}

    session_dir = Path.home() / ".milenium"
    session_dir.mkdir(parents=True, exist_ok=True)

    # Use first account for upload (must be admin in target)
    acc = accounts[0]
    api_id = int(acc.get("api_id", config.get("TG_API_ID", "")))
    api_hash = acc.get("api_hash", config.get("TG_API_HASH", ""))
    session = acc.get("session", DEFAULT_SESSION)

    client = TelegramClient(str(session_dir / session), api_id, api_hash)
    await client.start(phone=acc.get("phone"))
    me = await client.get_me()
    logger.progress(f"TG REUPLOAD: авторизован как {me.username or me.id}")

    target_cache = {}
    target_entity = await _resolve_target(client, target, target_cache)
    if not target_entity:
        await client.disconnect()
        return {"error": "could not resolve upload target"}

    files = [f for f in local_dir.rglob("*") if f.is_file() and _is_target_file(f)]
    files.sort(key=lambda x: x.stat().st_size)

    uploaded = 0
    failed = 0
    skipped_empty = 0
    for f in files:
        if f.stat().st_size == 0:
            skipped_empty += 1
            continue
        ok = await _send_file(client, target_entity, str(f), target_cache)
        if ok:
            uploaded += 1
            if delete_after:
                try:
                    f.unlink(missing_ok=True)
                    logger.progress(f"TG REUPLOAD: удалён локальный {f.name}")
                except Exception as e:
                    logger.progress(f"TG REUPLOAD: не удалён {f.name}: {e}")
        else:
            failed += 1

    await client.disconnect()
    return {"uploaded": uploaded, "failed": failed, "skipped_empty": skipped_empty, "total": len(files)}


def run_reupload(local_dir=None, accounts_file=None, target=None, delete_after=True):
    from milenium.constants import (
        ensure_layout,
        TG_DUMPS_DIR,
        TG_ACCOUNTS_FILE,
        TG_LIBRARY_TARGET,
    )

    ensure_layout()
    local_dir = local_dir or str(TG_DUMPS_DIR)
    accounts_file = accounts_file or str(TG_ACCOUNTS_FILE)
    target = target or TG_LIBRARY_TARGET
    return asyncio.run(reupload_local(local_dir, accounts_file, target, delete_after))
