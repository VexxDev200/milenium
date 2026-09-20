import aiohttp
from milenium.modules import config


async def check_physical(firstname: str, lastname: str, birthdate: str, region: int = 0) -> dict:
    token = config.get("FSSP_TOKEN", "")
    if not token:
        return {"error": "FSSP_TOKEN not set. Get free token: https://api-ip.fssprus.ru/register"}
    url = "https://api-ip.fssprus.ru/api/v1.0/search/physical"
    params = {
        "token": token,
        "firstname": firstname,
        "lastname": lastname,
        "birthdate": birthdate,
        "region": region,
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=20) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                data = await resp.json()
                return {
                    "status": data.get("status"),
                    "task": data.get("response", {}).get("task"),
                    "result": data.get("response", {}).get("result"),
                }
    except Exception as e:
        return {"error": str(e)}


async def check_legal(name: str) -> dict:
    token = config.get("FSSP_TOKEN", "")
    if not token:
        return {"error": "FSSP_TOKEN not set"}
    url = "https://api-ip.fssprus.ru/api/v1.0/search/legal"
    params = {"token": token, "name": name}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=20) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                data = await resp.json()
                return {"status": data.get("status"), "result": data.get("response", {})}
    except Exception as e:
        return {"error": str(e)}