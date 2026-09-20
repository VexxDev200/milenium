import os
from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest

API_ID = int(os.environ.get("TG_API_ID", "28088599"))
API_HASH = os.environ.get("TG_API_HASH", "8df5e438f9b66dba136e70a1e7a2edb4")
SESSION = "milenium"


async def check_user(username: str) -> dict:
    """Telethon: ID, имя, био, фото, статус."""
    if not API_ID or not API_HASH:
        return {"error": "TG_API_ID/TG_API_HASH not set"}
    try:
        async with TelegramClient(SESSION, API_ID, API_HASH) as client:
            entity = await client.get_entity(username)
            full = await client(GetFullUserRequest(entity))
            user = full.user
            return {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "username": user.username,
                "phone": user.phone,
                "bio": full.about,
                "status": str(user.status) if user.status else None,
            }
    except Exception as e:
        return {"error": str(e)}