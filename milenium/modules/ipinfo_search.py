import os
import aiohttp

from milenium.modules import config
IPINFO_TOKEN = config.get("IPINFO_TOKEN", "")


async def check(ip: str) -> dict:
    """ipinfo.io: гео, ASN, компания."""
    if not IPINFO_TOKEN:
        return {"error": "IPINFO_TOKEN not set"}
    url = f"https://ipinfo.io/{ip}/json?token={IPINFO_TOKEN}"
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
                    "timezone": data.get("timezone"),
                    "loc": data.get("loc"),
                }
    except Exception as e:
        return {"error": str(e)}