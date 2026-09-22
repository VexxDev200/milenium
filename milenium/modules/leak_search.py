import aiohttp
from milenium.modules import config


async def niamonx_search(query: str) -> dict:
    """NiamonX: поиск по 140B записей утечек."""
    key = config.get("NIAMONX_API_KEY", "")
    if not key:
        return {"error": "NIAMONX_API_KEY not set"}
    url = "https://dash.niamonx.io/api/v2/breaches_search"
    headers = {"Content-Type": "application/json", "X-API-Key": key}
    payload = {"query": query}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=20) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                data = await resp.json()
                return {
                    "found": data.get("found"),
                    "data": data.get("data"),
                    "risk": data.get("risk"),
                    "meta": data.get("meta"),
                }
    except Exception as e:
        return {"error": str(e)}


async def hibp_test(email: str) -> dict:
    """HIBP: бесплатный ключ, работает для тестовых аккаунтов."""
    key = config.get("HIBP_KEY", "00000000000000000000000000000000")
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}"
    headers = {"hibp-api-key": key, "User-Agent": "milenium/1.0"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=15) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"breaches": [b["Name"] for b in data]}
                elif resp.status == 404:
                    return {"breaches": []}
                else:
                    return {"error": f"HTTP {resp.status}"}
    except Exception as e:
        return {"error": str(e)}