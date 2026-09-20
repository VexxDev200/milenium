import aiohttp
from milenium.modules import config


async def check(ip: str) -> dict:
    token = config.get("IPINFO_TOKEN", "")
    if not token:
        return {"error": "IPINFO_TOKEN not set"}
    url = f"https://ipinfo.io/{ip}/json?token={token}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                data = await resp.json()
                return {
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country"),
                    "org": data.get("org"),
                }
    except Exception as e:
        return {"error": str(e)}