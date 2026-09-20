from telethon import TelegramClient
from telethon.tl.functions.users import GetFullUserRequest
from milenium.modules import config

SESSION = "milenium"


async def check_user(username: str) -> dict:
    api_id_raw = config.get("TG_API_ID", "")
    api_hash = config.get("TG_API_HASH", "")
    if not api_id_raw or not api_hash:
        return {"error": "TG_API_ID/TG_API_HASH not set"}
    try:
        api_id = int(api_id_raw)
    except ValueError:
        return {"error": "TG_API_ID must be int"}
    try:
        async with TelegramClient(SESSION, api_id, api_hash) as client:
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