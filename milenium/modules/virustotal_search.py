import os, aiohttp
VT_KEY = os.environ.get("VIRUSTOTAL_API_KEY", "13d811a2ffc3cac8af9a1c7d67affea81fb598a3f07473562adf176e6ff064ab")
import os
import aiohttp

VT_KEY = os.environ.get("VIRUSTOTAL_API_KEY", "")


async def check_ip(ip: str) -> dict:
    """VirusTotal: репутация IP."""
    if not VT_KEY:
        return {"error": "VIRUSTOTAL_API_KEY not set"}
    url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
    headers = {"x-apikey": VT_KEY}
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
                    "last_analysis_stats": attrs.get("last_analysis_stats", {}),
                }
    except Exception as e:
        return {"error": str(e)}


async def check_domain(domain: str) -> dict:
    """VirusTotal: репутация домена."""
    if not VT_KEY:
        return {"error": "VIRUSTOTAL_API_KEY not set"}
    url = f"https://www.virustotal.com/api/v3/domains/{domain}"
    headers = {"x-apikey": VT_KEY}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                data = await resp.json()
                attrs = data.get("data", {}).get("attributes", {})
                return {
                    "reputation": attrs.get("reputation"),
                    "registrar": attrs.get("registrar"),
                    "categories": attrs.get("categories", {}),
                }
    except Exception as e:
        return {"error": str(e)}