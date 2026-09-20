import os
import aiohttp

CENSYS_TOKEN = os.environ.get("CENSYS_TOKEN", "censys_UJptWhGQ_L57vdqJiF1FQEd1VtTVArqsX")


async def check_host(ip: str) -> dict:
    """Censys API: хосты, сервисы, TLS."""
    if not CENSYS_TOKEN:
        return {"error": "CENSYS_TOKEN not set"}
    url = f"https://search.censys.io/api/v2/hosts/{ip}"
    headers = {"Authorization": f"Bearer {CENSYS_TOKEN}"}
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
                    "os": result.get("operating_system", {}).get("product"),
                    "country": result.get("location", {}).get("country"),
                }
    except Exception as e:
        return {"error": str(e)}