import aiohttp
from milenium.modules import config


async def check_host(ip: str) -> dict:
    token = config.get("CENSYS_TOKEN", "")
    if not token:
        return {"error": "CENSYS_TOKEN not set"}
    url = f"https://search.censys.io/api/v2/hosts/{ip}"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status == 404:
                    return {"found": False}
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                data = await resp.json()
                result = data.get("result", {})
                services = result.get("services", [])
                return {
                    "services": [s.get("service_name") for s in services],
                    "ports": [s.get("port") for s in services],
                    "country": result.get("location", {}).get("country"),
                }
    except Exception as e:
        return {"error": str(e)}