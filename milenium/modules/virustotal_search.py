import aiohttp
from milenium.modules import config


async def check_ip(ip: str) -> dict:
    key = config.get("VIRUSTOTAL_API_KEY", "")
    if not key:
        return {"error": "VIRUSTOTAL_API_KEY not set"}
    url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
    headers = {"x-apikey": key}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                data = await resp.json()
                attrs = data.get("data", {}).get("attributes", {})
                return {
                    "reputation": attrs.get("reputation"),
                    "country": attrs.get("country"),
                    "as_owner": attrs.get("as_owner"),
                }
    except Exception as e:
        return {"error": str(e)}