import os
import aiohttp

SHODAN_KEY = os.environ.get("SHODAN_API_KEY", "klFb9nYLxrCeJ284OEAtuVUygwfVtgY1")


async def check_ip(ip: str) -> dict:
    """Shodan API: порты, баннеры, CVE, гео."""
    if not SHODAN_KEY:
        return {"error": "SHODAN_API_KEY not set"}
    url = f"https://api.shodan.io/shodan/host/{ip}?key={SHODAN_KEY}&minify=true"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=15) as resp:
                if resp.status == 404:
                    return {"found": False}
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                data = await resp.json()
                return {
                    "org": data.get("org"),
                    "os": data.get("os"),
                    "ports": data.get("ports", []),
                    "hostnames": data.get("hostnames", []),
                    "vulns": list(data.get("vulns", {}).keys()),
                    "country": data.get("country_name"),
                    "city": data.get("city"),
                }
    except Exception as e:
        return {"error": str(e)}