import csv
import json
import os
import re
import subprocess
import shutil
import asyncio
import aiofiles
from pathlib import Path
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest, CheckChatInviteRequest
from telethon.tl.types import ChatInviteAlready, PeerChannel, DocumentAttributeSticker, DocumentAttributeAnimated, DocumentAttributeVideo, InputMessagesFilterDocument
from telethon.errors import FloodWaitError, UserAlreadyParticipantError, InviteHashExpiredError
from milenium.modules import config, logger
from milenium.modules.gdrive_uploader import get_service, ensure_folder, upload_single_file
from milenium.modules.split_uploader import split_large_file
from milenium.modules.virus_check import check_file_vt


DEFAULT_SESSION = "milenium_tg_grab"
from milenium.constants import TG_LIBRARY_TARGET as MILENIUM_LIBRARY_TARGET
# Пропускаем медиа-мусор и торренты
SKIP_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".mp4", ".mp3", ".avi", ".mov", ".mkv", ".webm", ".torrent", ".pdf", ".epub", ".doc", ".docx", ".ppt", ".pptx"}
# Только расширения баз/данных/архивов
WHITE_EXTS = {".csv", ".db", ".sqlite", ".sqlite3", ".json", ".txt", ".sql", ".zip", ".rar", ".7z", ".tar", ".gz", ".tgz", ".bz2", ".xz", ".xlsx", ".xls", ".xml", ".html", ".htm", ".bin"}
TARGET_MIMES = {"text", "csv", "json", "zip", "rar", "7z", "tar", "gzip", "x-7z", "x-rar", "x-tar", "x-bzip", "octet-stream"}


def _parse_link(link: str):
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


def _target_key(target):
    if hasattr(target, "id"):
        return f"id:{target.id}"
    return str(target).strip().lower()


def load_accounts(accounts_file=None):
    if not accounts_file or not Path(accounts_file).exists():
        return [{
            "api_id": config.get("TG_API_ID", ""),
            "api_hash": config.get("TG_API_HASH", ""),
            "session": DEFAULT_SESSION,
            "phone": None,
        }]

    path = Path(accounts_file)
    accounts = []
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "accounts" in data:
            data = data["accounts"]
        if isinstance(data, dict):
            data = [data]
        accounts = data if isinstance(data, list) else []
    elif path.suffix.lower() == ".csv":
        with open(path, "r", encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                accounts.append(dict(row))
    else:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            accounts.append({
                "session": parts[0],
                "phone": parts[1] if len(parts) > 1 else None,
            })

    cfg_api_id = config.get("TG_API_ID", "")
    cfg_api_hash = config.get("TG_API_HASH", "")
    for i, acc in enumerate(accounts):
        if "session_name" in acc and "session" not in acc:
            acc["session"] = acc.pop("session_name")
        acc.setdefault("api_id", cfg_api_id)
        acc.setdefault("api_hash", cfg_api_hash)
        acc.setdefault("session", f"tg_grab_{i+1:02d}")
        acc.setdefault("phone", None)
    return accounts


async def _get_folder_channels(client, folder_name):
    """Возвращает список каналов (entities) из папки Telegram по названию."""
    from telethon.tl.functions.messages import GetDialogFiltersRequest
    try:
        res = await client(GetDialogFiltersRequest())
        filters = getattr(res, "filters", []) or []
    except Exception as e:
        logger.progress(f"TG: не удалось получить папки: {e}")
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
        logger.progress(f"TG: папка '{folder_name}' не найдена")
        return []

    peers = []
    for attr in ("include_peers", "pinned_peers", "exclude_peers"):
        peers.extend(getattr(chosen, attr, []) or [])

    channels = []
    for peer in peers:
        try:
            entity = await client.get_entity(peer)
            if hasattr(entity, "title"):  # только каналы/группы, не личные чаты
                channels.append(entity)
        except Exception as e:
            logger.progress(f"TG: пропущен peer в папке: {e}")
    logger.progress(f"TG: в папке '{folder_name}' найдено {len(channels)} каналов")
    return channels


async def _join(client, link):
    kind, value = _parse_link(link)
    if not kind:
        logger.progress(f"TG: непонятная ссылка {link}")
        return None
    try:
        if kind == "invite":
            try:
                res = await client(CheckChatInviteRequest(value))
                if isinstance(res, ChatInviteAlready):
                    return res.chat
            except Exception:
                pass
            try:
                updates = await client(ImportChatInviteRequest(value))
                entity = updates.chats[0] if updates.chats else None
                return entity
            except UserAlreadyParticipantError:
                res = await client(CheckChatInviteRequest(value))
                if isinstance(res, ChatInviteAlready):
                    return res.chat
                return None
        else:
            entity = await client.get_entity(value)
            await client(JoinChannelRequest(entity))
            return entity
    except InviteHashExpiredError:
        logger.progress(f"TG: ссылка протухла {link}")
        return None
    except FloodWaitError as e:
        logger.progress(f"TG: флуд {link}, жду {e.seconds}s")
        await asyncio.sleep(e.seconds)
        return await _join(client, link)
    except Exception as e:
        return None


def _mime_to_ext(mime):
    if not mime:
        return ".bin"
    mime = mime.lower()
    mapping = {
        "text/plain": ".txt",
        "text/csv": ".csv",
        "application/json": ".json",
        "application/xml": ".xml",
        "application/zip": ".zip",
        "application/x-rar-compressed": ".rar",
        "application/x-7z-compressed": ".7z",
        "application/x-tar": ".tar",
        "application/gzip": ".gz",
        "application/x-bzip2": ".bz2",
        "application/sqlite": ".sqlite",
    }
    for k, v in mapping.items():
        if mime in k or k in mime:
            return v
    return ".bin"


def _is_target_file(document, mime):
    if mime:
        ml = mime.lower()
        if any(x in ml for x in TARGET_MIMES):
            return True
        if ml.startswith("text/"):
            return True
        if ml.startswith("application/"):
            return True
    return False


def _is_real_file(message):
    if not message.media:
        return False
    document = getattr(message.media, "document", None)
    if not document:
        return False
    mime = (document.mime_type or "").lower()
    if "tgsticker" in mime or "x-tgsticker" in mime:
        return False
    for attr in getattr(document, "attributes", []) or []:
        if isinstance(attr, (DocumentAttributeSticker, DocumentAttributeAnimated)):
            return False
        if isinstance(attr, DocumentAttributeVideo) and getattr(attr, "round_message", False):
            return False
    if message.file and message.file.name:
        ext = Path(message.file.name).suffix.lower()
        if ext in SKIP_EXTS:
            return False
        if ext and ext not in WHITE_EXTS:
            logger.progress(f"TG: пропущен по расширению {message.file.name}")
            return False
    return _is_target_file(document, mime)


async def _download_file(message, output_dir, max_file_mb=0, min_file_mb=0):
    try:
        if not _is_real_file(message):
            return None, "skipped", message.id

        document = message.media.document
        mime = document.mime_type or ""
        size = getattr(document, "size", 0)

        fname = None
        if message.file and message.file.name:
            fname = message.file.name
        else:
            fname = f"file_{message.id}{_mime_to_ext(mime)}"

        ext = Path(fname).suffix.lower()
        if ext in SKIP_EXTS:
            return None, "skipped", message.id

        size_mb = size / 1024 / 1024 if size else 0
        if max_file_mb and size and size_mb > max_file_mb:
            logger.progress(f"TG: пропуск {fname} ({size_mb:.1f}MB > {max_file_mb}MB)")
            return None, "skipped", message.id
        if min_file_mb and size and size_mb < min_file_mb:
            logger.progress(f"TG: пропуск {fname} ({size_mb:.1f}MB < {min_file_mb}MB)")
            return None, "skipped", message.id

        dest = output_dir / fname
        counter = 1
        while dest.exists():
            stem = Path(fname).stem
            suffix = Path(fname).suffix
            dest = output_dir / f"{stem}_{counter:03d}{suffix}"
            counter += 1

        # Telethon download_media синхронно пишет на диск, но нам нужен путь
        await message.download_media(file=str(dest))
        logger.progress(f"TG: скачал {dest.name} ({(size//1024) if size else '?'}KB)")
        return str(dest), "downloaded", message.id
    except FloodWaitError as e:
        logger.progress(f"TG: флуд загрузки, жду {e.seconds}s")
        await asyncio.sleep(e.seconds)
        return None, "error", message.id
    except Exception as e:
        logger.progress(f"TG: ошибка загрузки: {e}")
        return None, "error", message.id


def _rclone_copy_file(local_file, remote_path, rclone_bin=None):
    bin_path = rclone_bin or shutil.which("rclone") or "rclone"
    try:
        subprocess.run(
            [bin_path, "copy", local_file, remote_path, "--progress"],
            capture_output=True, text=True, check=True, encoding="utf-8"
        )
        return True
    except Exception:
        return False


async def _resolve_upload_target(client, target, upload_cfg):
    peer_id = upload_cfg.get("tg_target_peer_id") if upload_cfg else None
    if peer_id:
        try:
            return await client.get_entity(PeerChannel(peer_id))
        except Exception:
            pass
    try:
        entity = await client.get_entity(target)
        if upload_cfg and hasattr(entity, "id"):
            upload_cfg["tg_target_peer_id"] = entity.id
        return entity
    except Exception:
        pass
    kind, value = _parse_link(target)
    if kind == "invite":
        return await _join(client, target)
    return None


async def _load_existing_files(client, target_entity, limit=5000):
    existing = set()
    try:
        async for msg in client.iter_messages(target_entity, limit=limit):
            if msg.file and msg.file.name:
                existing.add(msg.file.name.lower())
            if msg.text:
                existing.add(msg.text.strip().lower())
    except Exception as e:
        logger.progress(f"TG UPLOAD: не удалось загрузить список существующих: {e}")
    return existing


async def _tg_send_file(client, entity, path):
    cap = Path(path).name
    while True:
        try:
            await client.send_file(entity, path, caption=cap)
            return
        except FloodWaitError as e:
            logger.progress(f"TG UPLOAD: флуд {e.seconds}s, жду…")
            await asyncio.sleep(e.seconds)


async def _upload_and_delete(local_path, upload_cfg, tg_client=None, existing_names=None, virus_check=True):
    path_obj = Path(local_path)
    if virus_check:
        vt_res = check_file_vt(local_path)
        if vt_res.get("skipped"):
            logger.progress(f"VT: пропущен {path_obj.name}: {vt_res.get('error')}")
        elif not vt_res.get("clean", True):
            logger.progress(f"VT: ВИРУС {path_obj.name} — {vt_res.get('detections')}/{vt_res.get('total')}")
            path_obj.unlink(missing_ok=True)
            return {"virus": True, "result": vt_res}
        else:
            logger.progress(f"VT: чисто {path_obj.name}")

    uploaded = False
    if upload_cfg.get("gdrive_service"):
        try:
            upload_single_file(upload_cfg["gdrive_service"], local_path, upload_cfg["gdrive_folder_id"])
            uploaded = True
        except Exception:
            pass
    if not uploaded and upload_cfg.get("rclone_remote"):
        uploaded = _rclone_copy_file(local_path, upload_cfg["rclone_remote"], upload_cfg.get("rclone_bin"))
    if not uploaded and upload_cfg.get("tg_upload_target") and tg_client:
        try:
            target = upload_cfg["tg_upload_target"]
            entity = await _resolve_upload_target(tg_client, target, upload_cfg)
            if not entity:
                logger.progress(f"TG UPLOAD: не удалось разрешить target для {path_obj.name}")
            else:
                lower_name = path_obj.name.lower()
                if existing_names and lower_name in existing_names:
                    logger.progress(f"TG UPLOAD: пропущен дубликат {path_obj.name}")
                    uploaded = True
                else:
                    max_tg_size = 2040 * 1024 * 1024
                    if path_obj.stat().st_size > max_tg_size:
                        parts = split_large_file(local_path)
                        if parts:
                            for part in parts:
                                await _tg_send_file(tg_client, entity, part)
                                logger.progress(f"TG UPLOAD: отправлен часть {Path(part).name}")
                                if existing_names is not None:
                                    existing_names.add(Path(part).name.lower())
                                Path(part).unlink(missing_ok=True)
                            path_obj.unlink(missing_ok=True)
                            uploaded = True
                    else:
                        await _tg_send_file(tg_client, entity, local_path)
                        logger.progress(f"TG UPLOAD: отправлен {path_obj.name}")
                        uploaded = True
                        if existing_names is not None:
                            existing_names.add(lower_name)
        except FloodWaitError as e:
            logger.progress(f"TG UPLOAD: флуд {path_obj.name}, жду {e.seconds}s")
            await asyncio.sleep(e.seconds)
            return await _upload_and_delete(local_path, upload_cfg, tg_client, existing_names, virus_check=False)
        except Exception as e:
            logger.progress(f"TG UPLOAD: ошибка {path_obj.name}: {e}")

    if uploaded and upload_cfg.get("delete_local"):
        path_obj.unlink(missing_ok=True)
        logger.progress(f"TG: удалён локальный {path_obj.name}")

    return uploaded


def _topic_title(topic):
    # topic может быть ForumTopic или его производной
    title = getattr(topic, "title", None)
    if title:
        return title
    # страховка: иногда title внутри top_message
    top = getattr(topic, "top_message", None)
    if top:
        title = getattr(top, "message", None) or ""
        if not title:
            fwd = getattr(top, "fwd_from", None)
            if fwd:
                title = getattr(fwd, "from_name", "") or ""
    return title or ""


def _match_topic_name(topic, patterns):
    if not patterns:
        return True
    title = _topic_title(topic).lower()
    for pat in patterns:
        pat = pat.strip().lower()
        if pat and pat in title:
            return True
    return False


async def _iter_channel_messages(client, entity, limit_per_channel, topic_patterns=None):
    is_forum = getattr(entity, "forum", False)
    doc_filter = InputMessagesFilterDocument()
    if is_forum:
        try:
            from telethon.tl.functions.messages import GetForumTopicsRequest
            peer = await client.get_input_entity(entity)
            all_topics = []
            offset_topic = 0
            while True:
                res = await client(GetForumTopicsRequest(
                    peer=peer,
                    offset_date=None,
                    offset_id=0,
                    offset_topic=offset_topic,
                    limit=100,
                ))
                topics = getattr(res, "topics", [])
                if not topics:
                    break
                all_topics.extend(topics)
                offset_topic = getattr(topics[-1], "id", 0)
                if len(topics) < 100:
                    break

            if topic_patterns:
                matched = [t for t in all_topics if _match_topic_name(t, topic_patterns)]
                logger.progress(f"TG: форум, топиков всего {len(all_topics)}, по фильтру {len(matched)}")
                selected_topics = matched
            else:
                logger.progress(f"TG: форум, найдено {len(all_topics)} топиков")
                selected_topics = all_topics

            total_topics = len(selected_topics)
            for topic_idx, topic in enumerate(selected_topics, 1):
                tid = getattr(topic, "id", None)
                if tid is None:
                    continue
                ttitle = _topic_title(topic)
                if topic_idx == 1 or topic_idx % 10 == 0 or topic_idx == total_topics:
                    logger.progress(f"TG: топик {topic_idx}/{total_topics} (#{tid}) {ttitle}")
                file_count = 0
                async for message in client.iter_messages(entity, reply_to=tid, limit=limit_per_channel, filter=doc_filter):
                    file_count += 1
                    if file_count % 100 == 0:
                        logger.progress(f"TG: топик #{tid}, найдено {file_count} файлов")
                    yield message
                if file_count:
                    logger.progress(f"TG: топик #{tid} '{ttitle}' — {file_count} файлов")
            logger.progress(f"TG: форум, завершено {total_topics} топиков")
        except Exception as e:
            logger.progress(f"TG: ошибка чтения топиков: {e}")
    logger.progress(f"TG: обход общих сообщений канала")
    async for message in client.iter_messages(entity, limit=limit_per_channel, filter=doc_filter):
        yield message


async def _process_channel(client, link_or_entity, output_dir, limit_per_channel, max_file_mb=0, min_file_mb=0, upload_cfg=None, existing_names=None, topic_patterns=None):
    out = {"joined": False, "files": [], "errors": [], "media": 0, "done": 0}
    try:
        if hasattr(link_or_entity, "id"):
            # переполучаем entity текущим клиентом, чтобы access_hash был валиден
            entity = await client.get_entity(link_or_entity)
        else:
            entity = await _join(client, link_or_entity)
    except Exception as e:
        logger.progress(f"TG: не удалось получить канал {link_or_entity}: {e}")
        out["errors"].append(str(link_or_entity))
        return out
    if not entity:
        out["errors"].append(str(link_or_entity))
        return out
    out["joined"] = True

    async def _handle_message(message):
        if not message or not message.media:
            return

        fname = None
        if message.file and message.file.name:
            fname = message.file.name

        if upload_cfg and fname and upload_cfg.get("tg_upload_target") and existing_names:
            if fname.lower() in existing_names:
                logger.progress(f"TG: пропущен дубликат {fname}")
                return

        out["media"] += 1
        logger.progress(f"TG: найден файл #{message.id} {fname or 'noname'}")
        path, status, mid = await _download_file(message, output_dir, max_file_mb, min_file_mb)
        if status == "downloaded":
            out["done"] += 1
        if path:
            if upload_cfg:
                ok = await _upload_and_delete(path, upload_cfg, tg_client=client, existing_names=existing_names)
                virus = isinstance(ok, dict) and ok.get("virus")
                keep_local = virus or (not upload_cfg.get("delete_local") or not ok)
                if keep_local:
                    out["files"].append(path)
            else:
                out["files"].append(path)

    try:
        async for message in _iter_channel_messages(client, entity, limit_per_channel, topic_patterns=topic_patterns):
            await _handle_message(message)
    except FloodWaitError as e:
        logger.progress(f"TG: флуд канала {link_or_entity}, жду {e.seconds}s")
        await asyncio.sleep(e.seconds)
    except Exception as e:
        logger.progress(f"TG: ошибка канала {link_or_entity}: {e}")
        out["errors"].append(str(e))

    logger.progress(f"TG: канал {link_or_entity} готов — найдено {out['media']}, скачано {out['done']}")
    return out


def _rclone_sync(local_dir, remote_path, rclone_bin=None):
    bin_path = rclone_bin or shutil.which("rclone") or "rclone"
    try:
        result = subprocess.run(
            [bin_path, "sync", local_dir, remote_path, "--progress"],
            capture_output=True, text=True, check=True, encoding="utf-8"
        )
        return result.stdout
    except Exception as e:
        return {"error": str(e)}


async def grab_channels(links=None, output_dir="data/tg_dumps", limit_per_channel=500, max_file_mb=0, min_file_mb=0, accounts=None, rclone_remote=None, rclone_bin=None, gdrive_service_account=None, gdrive_folder="milenium_tg_dumps", delete_local=False, tg_upload_target=None, no_upload=False, topic_patterns=None, folder_name=None):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not accounts:
        return {"error": "no accounts"}

    upload_cfg = None
    if not no_upload and (gdrive_service_account or rclone_remote or tg_upload_target):
        upload_cfg = {
            "gdrive_service": None,
            "gdrive_folder_id": None,
            "rclone_remote": rclone_remote,
            "rclone_bin": rclone_bin,
            "delete_local": delete_local,
            "tg_upload_target": tg_upload_target,
        }
        if gdrive_service_account:
            try:
                service = get_service(gdrive_service_account)
                folder_id = ensure_folder(service, gdrive_folder)
                upload_cfg["gdrive_service"] = service
                upload_cfg["gdrive_folder_id"] = folder_id
                logger.progress(f"GDRIVE: готов, папка {gdrive_folder}")
            except Exception as e:
                logger.progress(f"GDRIVE: init failed: {e}")

    session_dir = Path.home() / ".milenium"
    session_dir.mkdir(parents=True, exist_ok=True)

    clients = []
    for acc in accounts:
        api_id = acc.get("api_id", "")
        api_hash = acc.get("api_hash", "")
        if not api_id or not api_hash:
            logger.progress(f"TG: пропуск {acc.get('session')} — нет api_id/api_hash")
            continue
        session_path = session_dir / acc["session"]
        client = TelegramClient(str(session_path), int(api_id), api_hash)
        phone = acc.get("phone")
        try:
            await client.start(phone=phone)
            me = await client.get_me()
            logger.progress(f"TG: авторизован {acc['session']} как {me.username or me.id}")
            clients.append(client)
        except Exception as e:
            logger.progress(f"TG: аккаунт {acc.get('session')} не стартовал: {e}")
            try:
                await client.disconnect()
            except Exception:
                pass
    if not clients:
        return {"error": "no authorized accounts"}

    targets = []
    seen = set()
    for link in links or []:
        key = _target_key(link)
        if key in seen:
            continue
        seen.add(key)
        targets.append(link)
    if folder_name:
        folder_channels = await _get_folder_channels(clients[0], folder_name)
        if not folder_channels and not targets:
            for c in clients:
                await c.disconnect()
            return {"error": f"folder '{folder_name}' not found or empty"}
        for ch in folder_channels:
            key = _target_key(ch)
            if key in seen:
                continue
            seen.add(key)
            targets.append(ch)
    if not targets:
        for c in clients:
            await c.disconnect()
        return {"error": "no targets"}
    logger.progress(f"TG: уникальных целей {len(targets)} (ссылки + папка «{folder_name or '-'}»)")

    results = {"joined": 0, "files": [], "errors": []}

    existing_names = set()
    if upload_cfg and upload_cfg.get("tg_upload_target"):
        try:
            target_entity = await _resolve_upload_target(clients[0], upload_cfg["tg_upload_target"], upload_cfg)
            if target_entity:
                existing_names = await _load_existing_files(clients[0], target_entity, limit=10000)
                logger.progress(f"TG UPLOAD: в target-канале уже {len(existing_names)} файлов")
        except Exception as e:
            logger.progress(f"TG UPLOAD: не удалось получить список файлов target: {e}")

    # ПАРАЛЛЕЛЬНАЯ обработка каналов — максимальная скорость
    async def run_for_target(i, target):
        last_error = None
        for offset in range(len(clients)):
            client = clients[(i + offset) % len(clients)]
            res = await _process_channel(client, target, output_dir, limit_per_channel, max_file_mb, min_file_mb, upload_cfg, existing_names, topic_patterns=topic_patterns)
            if res["joined"]:
                results["joined"] += 1
                results["files"].extend(res["files"])
                return
            else:
                last_error = res["errors"][-1] if res["errors"] else "unknown"
        results["errors"].append(f"{target}: все аккаунты отказали ({last_error})")

    await asyncio.gather(*[run_for_target(i, target) for i, target in enumerate(targets)])

    for client in clients:
        await client.disconnect()

    if rclone_remote and not delete_local:
        results["rclone"] = _rclone_sync(str(output_dir), rclone_remote, rclone_bin)

    return results


def run(links=None, output_dir=None, limit_per_channel=500, max_file_mb=0, min_file_mb=0, accounts_file=None, rclone_remote=None, rclone_bin=None, gdrive_service_account=None, gdrive_folder="milenium_tg_dumps", delete_local=False, tg_upload_target=None, no_upload=False, topic_patterns=None, folder_name=None):
    from milenium.constants import ensure_layout, TG_DUMPS_DIR, TG_ACCOUNTS_FILE

    ensure_layout()
    output_dir = output_dir or str(TG_DUMPS_DIR)
    accounts = load_accounts(accounts_file or str(TG_ACCOUNTS_FILE))
    return asyncio.run(grab_channels(
        links=links,
        output_dir=output_dir,
        limit_per_channel=limit_per_channel,
        max_file_mb=max_file_mb,
        min_file_mb=min_file_mb,
        accounts=accounts,
        rclone_remote=rclone_remote,
        rclone_bin=rclone_bin,
        gdrive_service_account=gdrive_service_account,
        gdrive_folder=gdrive_folder,
        delete_local=delete_local,
        tg_upload_target=tg_upload_target,
        no_upload=no_upload,
        topic_patterns=topic_patterns,
        folder_name=folder_name,
    ))
