import aiohttp
from milenium.modules import config


async def check(ip: str) -> dict:
    key = config.get("ABUSEIPDB_KEY", "")
    if not key:
        return {"error": "ABUSEIPDB_KEY not set"}
    url = "https://api.abuseipdb.com/api/v2/check"
    params = {"ipAddress": ip, "maxAgeInDays": 90}
    headers = {"Key": key, "Accept": "application/json"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers, timeout=15) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                data = await resp.json()
                d = data.get("data", {})
                return {
                    "abuse_score": d.get("abuseConfidenceScore"),
                    "total_reports": d.get("totalReports"),
                    "country": d.get("countryCode"),
                    "isp": d.get("isp"),
                }
    except Exception as e:
        return {"error": str(e)}