import json
import asyncio
import csv
from pathlib import Path
from collections import defaultdict
from telethon import TelegramClient
from telethon.tl.functions.messages import SearchGlobalRequest
from telethon.tl.types import InputPeerEmpty, Channel, InputMessagesFilterDocument, InputMessagesFilterEmpty
from telethon.errors import FloodWaitError
from milenium.modules import config, logger

DEFAULT_SESSION = "milenium_tg_grab"

# Запросы для поиска каналов с базами/сливами
# Короткий эффективный набор запросов
DEFAULT_QUERIES = [
    "database", "combolist", "leak", "dump", "data leak",
    "sql dump", "users database", "passwords",
    "base", "db dump", "data breach",
    "база", "слив", "утечка",
    "базы данных", "комболист",
    "почты", "пароли", "клиенты",
    "free database", "бесплатная база",
    "telegram leak", "channel database",
]


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


async def _search_with_client(client, queries, limit_per_query):
    found_local = defaultdict(lambda: {"title": "", "username": "", "count": 0, "queries": set(), "last_file": None})
    me = await client.get_me()
    logger.progress(f"TG SEARCH: аккаунт {me.username or me.id} — {len(queries)} запросов")

    for query in queries:
        logger.progress(f"TG SEARCH: запрос '{query}'")
        offset_id = 0
        offset_peer = InputPeerEmpty()
        offset_rate = 0
        total = 0
        while total < limit_per_query:
            try:
                res = await asyncio.wait_for(client(SearchGlobalRequest(
                    q=query,
                    filter=InputMessagesFilterEmpty(),
                    min_date=None,
                    max_date=None,
                    offset_rate=offset_rate,
                    offset_peer=offset_peer,
                    offset_id=offset_id,
                    limit=min(100, limit_per_query - total),
                )), timeout=45)
            except asyncio.TimeoutError:
                logger.progress(f"TG SEARCH: таймаут '{query}'")
                break
            except FloodWaitError as e:
                logger.progress(f"TG SEARCH: флуд {e.seconds}s на '{query}'")
                await asyncio.sleep(min(e.seconds, 30))
                continue
            except Exception as e:
                logger.progress(f"TG SEARCH: ошибка '{query}': {e}")
                break

            if not res.messages:
                break

            for msg in res.messages:
                peer = msg.peer_id
                cid = None
                if hasattr(peer, "channel_id"):
                    cid = peer.channel_id
                elif hasattr(peer, "chat_id"):
                    cid = peer.chat_id
                elif hasattr(peer, "user_id"):
                    continue

                if not cid:
                    continue

                username = ""
                title = ""
                try:
                    entity = await client.get_entity(peer)
                    if isinstance(entity, Channel):
                        username = entity.username or ""
                        title = entity.title or ""
                    else:
                        continue
                except Exception:
                    continue

                key = str(cid)
                found_local[key]["id"] = cid
                found_local[key]["title"] = title or found_local[key]["title"]
                found_local[key]["username"] = username or found_local[key]["username"]
                found_local[key]["count"] += 1
                found_local[key]["queries"].add(query)
                if msg.file and msg.file.name:
                    found_local[key]["last_file"] = msg.file.name

            last = res.messages[-1]
            offset_id = last.id
            offset_peer = last.peer_id
            offset_rate = getattr(res, "next_rate", 0) or 0
            total += len(res.messages)
            if len(res.messages) < 100:
                break

    return found_local


async def _check_channel_files(client, channel_id, sample_limit=10):
    """Проверяет, есть ли в канале файлы. Возвращает список имен файлов-примеров."""
    samples = []
    try:
        entity = await client.get_entity(channel_id)
        async for msg in client.iter_messages(entity, limit=sample_limit, filter=InputMessagesFilterDocument()):
            if msg.file and msg.file.name:
                samples.append(msg.file.name)
    except Exception as e:
        logger.progress(f"TG SEARCH: не удалось проверить файлы канала {channel_id}: {e}")
    return samples


async def search_channels(queries=None, accounts=None, limit_per_query=200, min_mentions=1, check_files=True, file_sample=5):
    if not queries:
        queries = DEFAULT_QUERIES
    if not accounts:
        return {"error": "no accounts"}

    session_dir = Path.home() / ".milenium"
    session_dir.mkdir(parents=True, exist_ok=True)

    # Используем первый аккаунт для поиска — стабильнее, чем параллельная авторизация
    acc = accounts[0]
    api_id = int(acc.get("api_id", config.get("TG_API_ID", "")))
    api_hash = acc.get("api_hash", config.get("TG_API_HASH", ""))
    session_name = acc.get("session", DEFAULT_SESSION)

    client = TelegramClient(str(session_dir / session_name), api_id, api_hash)
    try:
        await client.start(phone=acc.get("phone"))
        me = await client.get_me()
        logger.progress(f"TG SEARCH: авторизован как {me.username or me.id}")

        found = await _search_with_client(client, queries, limit_per_query)

        # Фильтруем по min_mentions
        filtered = {k: v for k, v in found.items() if v["count"] >= min_mentions}
        logger.progress(f"TG SEARCH: найдено уникальных каналов {len(filtered)}")

        if check_files:
            check_tasks = []
            cids = list(filtered.keys())
            for cid in cids:
                check_tasks.append(_check_channel_files(client, filtered[cid]["id"], file_sample))
            file_samples = await asyncio.gather(*check_tasks)
            for cid, samples in zip(cids, file_samples):
                filtered[cid]["file_samples"] = samples
                filtered[cid]["has_files"] = len(samples) > 0
    finally:
        await client.disconnect()

    results = []
    for cid, v in filtered.items():
        results.append({
            "id": v.get("id"),
            "title": v["title"],
            "username": v["username"],
            "mentions": v["count"],
            "queries": sorted(v["queries"]),
            "last_file": v.get("last_file"),
            "file_samples": v.get("file_samples", []),
            "has_files": v.get("has_files", None),
            "link": f"https://t.me/{v['username']}" if v["username"] else f"https://t.me/c/{v.get('id')}",
        })
    results.sort(key=lambda x: x["mentions"], reverse=True)
    return results


def run(queries=None, accounts_file=None, limit_per_query=200, min_mentions=1,
        check_files=True, file_sample=5, output=None):
    from milenium.constants import ensure_layout, TG_ACCOUNTS_FILE, TG_SEARCH_JSON

    ensure_layout()
    accounts_file = accounts_file or str(TG_ACCOUNTS_FILE)
    output = output or str(TG_SEARCH_JSON)
    accounts = load_accounts(accounts_file)
    if queries and isinstance(queries, str):
        queries = [q.strip() for q in queries.split(",") if q.strip()]
    results = asyncio.run(search_channels(
        queries=queries,
        accounts=accounts,
        limit_per_query=limit_per_query,
        min_mentions=min_mentions,
        check_files=check_files,
        file_sample=file_sample,
    ))
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.progress(f"TG SEARCH: сохранено {len(results)} каналов в {out}")
    return {"count": len(results), "path": str(out), "top": results[:20]}
