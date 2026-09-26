import json
import asyncio
import csv
import re
from pathlib import Path
from telethon import TelegramClient
from telethon.tl.functions.messages import GetDialogFiltersRequest
from telethon.tl.types import InputMessagesFilterDocument
from telethon.errors import FloodWaitError
from milenium.modules import config, logger

DEFAULT_SESSION = "milenium_tg_grab"

BASE_EXTS = {
    ".csv", ".db", ".sqlite", ".sqlite3", ".json", ".txt", ".sql",
    ".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz",
    ".xlsx", ".xls", ".xml",
}

# Явный мусор — не базы
SKIP_EXTS = {".torrent", ".pdf", ".epub", ".doc", ".docx", ".ppt", ".pptx", ".md"}
SKIP_NAME_RE = re.compile(
    r"(manual|prompt|cursor|claude|kimi|rfx|\.md$|torrent|udemy|course|video|clip|edit)",
    re.I,
)
BASE_NAME_RE = re.compile(
    r"(database|data.?base|db|dump|leak|combo|sql|base|баз|слив|утеч|users?|pass|mail|phone|"
    r"csv|\.7z|\.rar|\.zip|\.sql|\.db|\.sqlite|xlsx|customers?|clients?)",
    re.I,
)


def load_accounts(accounts_file=None):
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


def _is_base_file(filename):
    if not filename:
        return False
    name = filename.strip()
    ext = Path(name).suffix.lower()
    if ext in SKIP_EXTS:
        return False
    if SKIP_NAME_RE.search(name):
        return False
    if ext in BASE_EXTS:
        return True
    if BASE_NAME_RE.search(name):
        return True
    return False


async def _get_folder_channels(client, folder_name):
    try:
        res = await client(GetDialogFiltersRequest())
        filters = getattr(res, "filters", []) or []
    except Exception as e:
        logger.progress(f"TG SCAN: не удалось получить папки: {e}")
        return []

    target = folder_name.strip().lower()
    chosen = None
    for f in filters:
        title = getattr(f, "title", "") or ""
        title_text = title.text if hasattr(title, "text") else str(title)
        if target in title_text.strip().lower():
            chosen = f
            break
    if not chosen:
        logger.progress(f"TG SCAN: папка '{folder_name}' не найдена")
        return []

    peers = []
    for attr in ("include_peers", "pinned_peers"):
        peers.extend(getattr(chosen, attr, []) or [])

    channels = []
    for peer in peers:
        try:
            entity = await client.get_entity(peer)
            if hasattr(entity, "title"):
                channels.append(entity)
        except Exception:
            pass

    # Сначала обычные каналы (быстро), форумы в конце
    channels.sort(key=lambda e: (getattr(e, "forum", False), e.title or ""))
    logger.progress(f"TG SCAN: в папке '{folder_name}' {len(channels)} каналов")
    return channels


def _topic_title(topic):
    title = getattr(topic, "title", None)
    if title:
        return title.text if hasattr(title, "text") else str(title)
    return f"#{getattr(topic, 'id', '?')}"


async def _scan_forum_topics(client, entity, sample_limit, prefix, ch_label, max_topics):
    from telethon.tl.functions.messages import GetForumTopicsRequest

    bases = []
    topic_hits = []
    total_files = 0
    per_topic = max(8, min(sample_limit, 25))
    seen_topic_ids = set()

    logger.progress(f"TG SCAN: {prefix}   форум «{ch_label}» — загрузка топиков…")
    try:
        peer = await asyncio.wait_for(client.get_input_entity(entity), timeout=25)
    except Exception as e:
        logger.progress(f"TG SCAN: {prefix}   skip форум (peer): {e}")
        return bases, total_files, topic_hits

    offset_topic = 0
    pages = 0
    scanned_topics = 0

    while scanned_topics < max_topics:
        try:
            res = await asyncio.wait_for(
                client(GetForumTopicsRequest(
                    peer=peer,
                    offset_date=None,
                    offset_id=0,
                    offset_topic=offset_topic,
                    limit=100,
                )),
                timeout=45,
            )
        except asyncio.TimeoutError:
            logger.progress(f"TG SCAN: {prefix}   таймаут списка топиков, иду дальше")
            break
        except Exception as e:
            logger.progress(f"TG SCAN: {prefix}   ошибка списка топиков: {e}")
            break

        topics = getattr(res, "topics", []) or []
        if not topics:
            break

        pages += 1
        new_in_page = 0
        last_tid = offset_topic

        for topic in topics:
            if scanned_topics >= max_topics:
                break
            tid = getattr(topic, "id", None)
            if tid is None or tid in seen_topic_ids:
                continue
            seen_topic_ids.add(tid)
            new_in_page += 1
            scanned_topics += 1
            last_tid = tid

            ttitle = _topic_title(topic)
            logger.progress(f"TG SCAN: {prefix}   топик {scanned_topics}/{max_topics} «{ttitle}»")

            topic_files = 0
            topic_bases = []
            try:
                async for msg in client.iter_messages(
                    entity,
                    reply_to=tid,
                    limit=per_topic,
                    filter=InputMessagesFilterDocument(),
                ):
                    total_files += 1
                    topic_files += 1
                    fname = msg.file.name if msg.file and msg.file.name else f"file_{msg.id}"
                    if _is_base_file(fname):
                        topic_bases.append(fname)
                        logger.progress(f"TG SCAN: {prefix}     ✓ база [{ttitle}] {fname}")
            except FloodWaitError as e:
                wait = min(e.seconds, 20)
                logger.progress(f"TG SCAN: {prefix}     флуд, жду {wait}s")
                await asyncio.sleep(wait)
            except Exception as e:
                logger.progress(f"TG SCAN: {prefix}     ошибка топик «{ttitle}»: {e}")

            if topic_bases:
                bases.extend(topic_bases)
                topic_hits.append({
                    "topic": ttitle,
                    "topic_id": tid,
                    "base_count": len(topic_bases),
                    "samples": topic_bases[:10],
                })

        logger.progress(
            f"TG SCAN: {prefix}   страница #{pages}: новых топиков {new_in_page}, всего {scanned_topics}"
        )

        if new_in_page == 0:
            logger.progress(f"TG SCAN: {prefix}   дубликаты топиков — стоп пагинации")
            break
        if len(topics) < 100:
            break
        if last_tid == offset_topic:
            logger.progress(f"TG SCAN: {prefix}   offset не сдвинулся — стоп")
            break
        offset_topic = last_tid

    logger.progress(
        f"TG SCAN: {prefix}   форум «{ch_label}» — {scanned_topics} топиков, "
        f"{len(bases)} баз, {len(topic_hits)} топиков с базами"
    )
    return bases, total_files, topic_hits


async def _scan_channel_body(client, entity, sample_limit, prefix, ch_label, max_topics):
    bases = []
    total_files = 0
    topic_hits = []
    is_forum = getattr(entity, "forum", False)

    if is_forum:
        try:
            entity = await asyncio.wait_for(client.get_entity(entity), timeout=25)
        except Exception as e:
            logger.progress(f"TG SCAN: {prefix}   refresh entity: {e}")
        bases, total_files, topic_hits = await _scan_forum_topics(
            client, entity, sample_limit, prefix, ch_label, max_topics
        )
    else:
        logger.progress(f"TG SCAN: {prefix}   читаю до {sample_limit} документов…")
        checked = 0
        async for msg in client.iter_messages(
            entity, limit=sample_limit, filter=InputMessagesFilterDocument()
        ):
            total_files += 1
            checked += 1
            fname = msg.file.name if msg.file and msg.file.name else f"file_{msg.id}"
            if _is_base_file(fname):
                bases.append(fname)
                logger.progress(f"TG SCAN: {prefix}     ✓ база {fname}")

    unique_bases = list(dict.fromkeys(bases))
    verdict = "none"
    if len(unique_bases) >= 5 or (is_forum and len(topic_hits) >= 2):
        verdict = "strong"
    elif len(unique_bases) >= 1:
        verdict = "yes"

    status = f"verdict={verdict}, {len(unique_bases)} баз / {total_files} файлов"
    logger.progress(f"TG SCAN: {prefix} ◀ «{ch_label}» — {status}")

    return {
        "id": entity.id,
        "title": getattr(entity, "title", ""),
        "username": getattr(entity, "username", None),
        "is_forum": is_forum,
        "verdict": verdict,
        "total_files_checked": total_files,
        "base_count": len(unique_bases),
        "base_samples": unique_bases[:25],
        "topics_with_bases": topic_hits[:30],
        "has_bases": len(unique_bases) > 0,
        "link": f"https://t.me/{entity.username}" if getattr(entity, "username", None) else f"https://t.me/c/{entity.id}",
    }


async def _scan_channel(client, entity, sample_limit, ch_idx, ch_total, max_topics, channel_timeout):
    ch_label = entity.title or str(entity.id)
    prefix = f"[{ch_idx}/{ch_total}]"
    logger.progress(
        f"TG SCAN: {prefix} ▶ «{ch_label}»"
        + (" [форум]" if getattr(entity, "forum", False) else "")
        + f" (лимит {channel_timeout}s)"
    )
    try:
        return await asyncio.wait_for(
            _scan_channel_body(client, entity, sample_limit, prefix, ch_label, max_topics),
            timeout=channel_timeout,
        )
    except asyncio.TimeoutError:
        logger.progress(f"TG SCAN: {prefix} ⏱ таймаут канала «{ch_label}» — пропуск, следующий")
        return {
            "id": entity.id,
            "title": getattr(entity, "title", ""),
            "username": getattr(entity, "username", None),
            "is_forum": getattr(entity, "forum", False),
            "verdict": "timeout",
            "total_files_checked": 0,
            "base_count": 0,
            "base_samples": [],
            "topics_with_bases": [],
            "has_bases": False,
            "skipped": True,
            "link": f"https://t.me/{entity.username}" if getattr(entity, "username", None) else f"https://t.me/c/{entity.id}",
        }
    except Exception as e:
        logger.progress(f"TG SCAN: {prefix} ошибка «{ch_label}»: {e} — следующий")
        return {
            "id": entity.id,
            "title": ch_label,
            "verdict": "error",
            "base_count": 0,
            "has_bases": False,
            "error": str(e),
        }


async def scan_folder(
    folder_name,
    accounts=None,
    sample_limit=50,
    min_bases=1,
    max_topics=120,
    channel_timeout=240,
):
    if not accounts:
        return {"error": "no accounts"}

    session_dir = Path.home() / ".milenium"
    session_dir.mkdir(parents=True, exist_ok=True)

    acc = accounts[0]
    api_id = int(acc.get("api_id", config.get("TG_API_ID", "")))
    api_hash = acc.get("api_hash", config.get("TG_API_HASH", ""))
    session_name = acc.get("session", DEFAULT_SESSION)

    client = TelegramClient(str(session_dir / session_name), api_id, api_hash)
    await client.start(phone=acc.get("phone"))
    me = await client.get_me()
    logger.progress(f"TG SCAN: авторизован как {me.username or me.id}")

    channels = await _get_folder_channels(client, folder_name)
    if not channels:
        await client.disconnect()
        return {"error": f"folder '{folder_name}' empty or not found"}

    logger.progress(
        f"TG SCAN: {len(channels)} каналов, sample={sample_limit}, "
        f"max_topics={max_topics}, timeout/канал={channel_timeout}s"
    )

    results = []
    with_bases = 0
    for idx, entity in enumerate(channels, 1):
        info = await _scan_channel(
            client, entity, sample_limit, idx, len(channels), max_topics, channel_timeout
        )
        if info.get("has_bases"):
            with_bases += 1
        if info.get("base_count", 0) >= min_bases:
            results.append(info)
        logger.progress(f"TG SCAN: === каналы {idx}/{len(channels)} | с базами: {with_bases} ===")

    await client.disconnect()
    results.sort(key=lambda x: (x.get("verdict") != "strong", -x.get("base_count", 0)))
    return results


def run(
    folder_name,
    accounts_file=None,
    sample_limit=50,
    min_bases=1,
    max_topics=120,
    channel_timeout=240,
    output=None,
):
    from milenium.constants import (
        ensure_layout,
        TG_ACCOUNTS_4_FILE,
        TG_FOLDER_SCAN_JSON,
    )

    ensure_layout()
    accounts_file = accounts_file or str(TG_ACCOUNTS_4_FILE)
    output = output or str(TG_FOLDER_SCAN_JSON)
    accounts = load_accounts(accounts_file)
    results = asyncio.run(
        scan_folder(
            folder_name,
            accounts,
            sample_limit,
            min_bases,
            max_topics=max_topics,
            channel_timeout=channel_timeout,
        )
    )
    if isinstance(results, dict) and results.get("error"):
        return results

    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    strong = [r for r in results if r.get("verdict") == "strong"]
    yes = [r for r in results if r.get("verdict") == "yes"]
    logger.progress(
        f"TG SCAN: ИТОГ — strong={len(strong)}, yes={len(yes)}, "
        f"всего с базами={len(strong) + len(yes)}"
    )
    return {
        "scanned": len(results),
        "strong": len(strong),
        "yes": len(yes),
        "with_bases": len(strong) + len(yes),
        "path": str(out),
        "top": (strong + yes)[:25],
    }
