import os
import aiohttp

ABUSE_KEY = os.environ.get("ABUSEIPDB_KEY", "94db3ce71663f504837d43de1f027fdd4a6f565d5b5e946d9337100e3849679960dbca271b6c97fe")


async def check(ip: str) -> dict:
    """AbuseIPDB: жалобы на IP."""
    if not ABUSE_KEY:
        return {"error": "ABUSEIPDB_KEY not set"}
    url = "https://api.abuseipdb.com/api/v2/check"
    params = {"ipAddress": ip, "maxAgeInDays": 90}
    headers = {"Key": ABUSE_KEY, "Accept": "application/json"}
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
                    "domain": d.get("domain"),
                }
    except Exception as e:
        return {"error": str(e)}