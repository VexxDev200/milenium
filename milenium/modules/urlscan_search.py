import aiohttp
from milenium.modules import config


async def check(url: str) -> dict:
    key = config.get("URLSCAN_API_KEY", "")
    if not key:
        return {"error": "URLSCAN_API_KEY not set"}
    api = "https://urlscan.io/api/v1/scan/"
    headers = {"API-Key": key, "Content-Type": "application/json"}
    payload = {"url": url, "visibility": "public"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api, headers=headers, json=payload, timeout=20) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                data = await resp.json()
                return {"result": data.get("result"), "uuid": data.get("uuid")}
    except Exception as e:
        return {"error": str(e)}