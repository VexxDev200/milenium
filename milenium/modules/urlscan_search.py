import os
import aiohttp

URLSCAN_KEY = os.environ.get("URLSCAN_API_KEY", "01a0be3c-70ce-71ec-b565-33ec1081fa30")


async def check(url: str) -> dict:
    """urlscan.io: скриншот и анализ сайта."""
    if not URLSCAN_KEY:
        return {"error": "URLSCAN_API_KEY not set"}
    api = "https://urlscan.io/api/v1/scan/"
    headers = {"API-Key": URLSCAN_KEY, "Content-Type": "application/json"}
    payload = {"url": url, "visibility": "public"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(api, headers=headers, json=payload, timeout=20) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                data = await resp.json()
                return {
                    "result": data.get("result"),
                    "uuid": data.get("uuid"),
                    "api": data.get("api"),
                }
    except Exception as e:
        return {"error": str(e)}