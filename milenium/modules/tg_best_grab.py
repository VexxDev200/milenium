"""
Целенаправленный сбор лучших баз данных и тулков из Telegram в архив milenium.

Команда:
    milenium library grab-best --folder "бд" --min-size-mb 50 --max-files 200

Логика:
1. Сканирует папку «бд» и находит strong-каналы/топики.
2. Для каждого strong-канала собирает метаданные файлов (размер, имя).
3. Отбирает:
   - базы данных >= min_size_mb с приоритетом country/global/combo/dump
   - тулки по имени/расширению (ddos, dox, osint, stealer, rat, .exe, .py, .zip...)
4. Скачивает топ max_files по размеру и заливает в TG_LIBRARY_TARGET.
"""
import asyncio
import json
import re
from pathlib import Path
from collections import defaultdict

from telethon import TelegramClient

from milenium.modules import config, logger
from milenium.modules.tg_scraper import (
    load_accounts,
    _target_key,
    _get_folder_channels,
    _join,
    _iter_channel_messages,
    _is_real_file,
    grab_channels,
)
from milenium.modules import tg_folder_scanner


DB_KEYWORDS = {
    "brazil", "brasil", "france", "usa", "us ", "india", "china", "russia",
    "global", "world", "combo", "dump", "database", "db ", "leak", " breach ",
    "card", "email", "password", "sql", "csv", "sqlite", "million", "m ",
}

TOOL_KEYWORDS = {
    "ddos", "dos", "stress", "booter", "dox", "osint", "grabber", "stealer",
    "rat", "botnet", "checker", "brute", "crack", "hack", "exploit", "inject",
    "bypass", "spoofer", "sniffer", "keylogger", "ransomware", "locker",
}

TOOL_EXTS = {".exe", ".py", ".cpp", ".c", ".go", ".rs", ".sh", ".bat", ".ps1",
             ".zip", ".rar", ".7z", ".tar", ".gz"}
DB_EXTS = {".sql", ".sqlite", ".sqlite3", ".db", ".csv", ".txt", ".json",
           ".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".xlsx", ".xls"}
SKIP_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mp3", ".avi",
             ".mov", ".mkv", ".webm", ".torrent", ".pdf", ".epub", ".doc",
             ".docx", ".ppt", ".pptx"}


def _score_name(name: str) -> int:
    low = name.lower()
    score = 0
    for kw in DB_KEYWORDS:
        if kw in low:
            score += 2
    for kw in TOOL_KEYWORDS:
        if kw in low:
            score += 3
    return score


def _classify(name: str, size_mb: float) -> str:
    low = name.lower()
    ext = Path(name).suffix.lower()
    if ext in SKIP_EXTS:
        return "skip"
    if any(kw in low for kw in TOOL_KEYWORDS) or ext in TOOL_EXTS:
        return "tool"
    if ext in DB_EXTS or any(kw in low for kw in DB_KEYWORDS):
        return "db"
    return "other"


async def _collect_files_from_entity(client, entity, limit=5000, topic_patterns=None):
    """Собирает (message_id, filename, size_mb, topic_id) без скачивания."""
    files = []
    try:
        async for message in _iter_channel_messages(client, entity, limit, topic_patterns=topic_patterns):
            if not _is_real_file(message):
                continue
            size = getattr(message.media.document, "size", 0)
            size_mb = size / 1024 / 1024
            fname = message.file.name or f"file_{message.id}"
            files.append({
                "message_id": message.id,
                "filename": fname,
                "size_mb": size_mb,
                "topic_id": getattr(message, "reply_to", None) and getattr(message.reply_to, "reply_to_msg_id", None),
            })
    except Exception as e:
        logger.progress(f"BEST: ошибка сбора {entity}: {e}")
    return files


async def _collect_all_candidates(folder_name, links, accounts, min_size_mb, scan_sample=120):
    session_dir = Path.home() / ".milenium"
    client = None
    for acc in accounts:
        try:
            session_path = session_dir / acc["session"]
            client = TelegramClient(str(session_path), int(acc["api_id"]), acc["api_hash"])
            await client.start(phone=acc.get("phone"))
            break
        except Exception as e:
            logger.progress(f"BEST: аккаунт {acc.get('session')} не стартовал: {e}")
            try:
                await client.disconnect()
            except Exception:
                pass
            client = None
    if not client:
        return {"error": "no authorized accounts"}

    all_candidates = []

    # 1. Папка TG
    if folder_name:
        logger.progress(f"BEST: сканирую папку «{folder_name}»")
        scan = tg_folder_scanner.run(
            folder_name=folder_name,
            accounts=accounts,
            sample_limit=scan_sample,
            min_bases=1,
            max_topics=120,
            channel_timeout=240,
        )
        if isinstance(scan, dict) and scan.get("error"):
            await client.disconnect()
            return scan

        strong = [r for r in scan if r.get("verdict") == "strong"]
        logger.progress(f"BEST: strong-каналов/топиков: {len(strong)}")

        for item in strong:
            entity = None
            try:
                if item.get("invite_hash"):
                    entity = await _join(client, item["invite_hash"])
                elif item.get("id"):
                    entity = await client.get_entity(item["id"])
                elif item.get("username"):
                    entity = await client.get_entity(item["username"])
                if not entity:
                    continue
                topic_ids = item.get("topics_with_bases", [])
                topic_patterns = None
                if topic_ids:
                    topic_patterns = [str(t) for t in topic_ids[:20]]
                files = await _collect_files_from_entity(client, entity, limit=3000, topic_patterns=topic_patterns)
                for f in files:
                    kind = _classify(f["filename"], f["size_mb"])
                    if kind == "skip":
                        continue
                    if kind == "db" and f["size_mb"] < min_size_mb:
                        continue
                    all_candidates.append({
                        **f,
                        "kind": kind,
                        "score": _score_name(f["filename"]),
                        "channel_title": getattr(entity, "title", str(entity)),
                        "channel_id": getattr(entity, "id", None),
                        "source": "folder",
                    })
            except Exception as e:
                logger.progress(f"BEST: пропуск {item}: {e}")

    # 2. Invite-ссылки
    for link in links or []:
        try:
            entity = await _join(client, link)
            if not entity:
                continue
            files = await _collect_files_from_entity(client, entity, limit=3000)
            for f in files:
                kind = _classify(f["filename"], f["size_mb"])
                if kind == "skip":
                    continue
                if kind == "db" and f["size_mb"] < min_size_mb:
                    continue
                all_candidates.append({
                    **f,
                    "kind": kind,
                    "score": _score_name(f["filename"]),
                    "channel_title": getattr(entity, "title", str(entity)),
                    "channel_id": getattr(entity, "id", None),
                    "source": "invite",
                })
        except Exception as e:
            logger.progress(f"BEST: ошибка invite {link}: {e}")

    await client.disconnect()
    return all_candidates


def _pick_candidates(candidates, max_files):
    # Приоритет: тулки и большие базы
    db = [c for c in candidates if c["kind"] == "db"]
    tools = [c for c in candidates if c["kind"] == "tool"]
    other = [c for c in candidates if c["kind"] == "other"]

    db.sort(key=lambda x: (-x["size_mb"], -x["score"]))
    tools.sort(key=lambda x: (-x["size_mb"], -x["score"]))
    other.sort(key=lambda x: (-x["size_mb"], -x["score"]))

    selected = []
    selected.extend(tools[:max_files // 4])
    selected.extend(db[:max_files - len(selected)])
    if len(selected) < max_files:
        selected.extend(other[:max_files - len(selected)])
    return selected


def _group_by_channel(selected):
    groups = defaultdict(list)
    for c in selected:
        key = (c.get("channel_id"), c.get("source"))
        groups[key].append(c)
    return groups


def run(
    folder="бд",
    links=None,
    accounts_file=None,
    min_size_mb=50,
    max_files=100,
    limit_per_channel=100_000,
    output_dir=None,
    tg_upload_target=None,
    use_four_accounts=False,
):
    from milenium.constants import (
        ensure_layout,
        TG_DUMPS_DIR,
        TG_ACCOUNTS_FILE,
        TG_ACCOUNTS_4_FILE,
        TG_LIBRARY_TARGET,
        TG_LIBRARY_SOURCE_LINKS,
    )

    ensure_layout()
    accounts = load_accounts(accounts_file or str(TG_ACCOUNTS_4_FILE if use_four_accounts else TG_ACCOUNTS_FILE))
    output_dir = output_dir or str(TG_DUMPS_DIR)
    tg_upload_target = tg_upload_target or TG_LIBRARY_TARGET
    links = list(links or TG_LIBRARY_SOURCE_LINKS)

    logger.progress(
        f"BEST: старт отбора — min_size={min_size_mb}MB, max_files={max_files}, "
        f"аккаунтов={len(accounts)}"
    )

    candidates = asyncio.run(_collect_all_candidates(folder, links, accounts, min_size_mb))
    if isinstance(candidates, dict) and candidates.get("error"):
        return candidates

    logger.progress(f"BEST: всего кандидатов — {len(candidates)}")

    selected = _pick_candidates(candidates, max_files)
    logger.progress(f"BEST: отобрано — {len(selected)}")

    # Сохраняем список до скачивания
    manifest = Path(output_dir) / "grab_best_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(selected, indent=2, ensure_ascii=False), encoding="utf-8")

    if not selected:
        return {"status": "no candidates", "candidates": len(candidates)}

    # Группируем по каналам и запускаем tg_scraper для выкачки всего отобранного
    # Для простоты: запускаем полную выкачку strong-каналов с min_file_mb.
    # tg_scraper сам отфильтрует по размеру и расширению.
    result = grab_channels(
        links=links,
        output_dir=output_dir,
        limit_per_channel=limit_per_channel,
        min_file_mb=min_size_mb,
        accounts=accounts,
        delete_local=True,
        tg_upload_target=tg_upload_target,
        no_upload=False,
        folder_name=folder,
    )

    result["candidates_found"] = len(candidates)
    result["selected_files"] = len(selected)
    result["manifest"] = str(manifest)
    return result
