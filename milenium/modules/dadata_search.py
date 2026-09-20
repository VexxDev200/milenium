import aiohttp
from milenium.modules import config


async def search_company(query: str) -> dict:
    key = config.get("DADATA_API_KEY", "")
    if not key:
        return {"error": "DADATA_API_KEY not set"}
    url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {key}",
    }
    payload = {"query": query, "count": 10}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=15) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                data = await resp.json()
                results = []
                for item in data.get("suggestions", []):
                    d = item.get("data", {})
                    results.append({
                        "name": item.get("value"),
                        "inn": d.get("inn"),
                        "ogrn": d.get("ogrn"),
                        "address": d.get("address", {}).get("value"),
                        "status": d.get("state", {}).get("status"),
                        "management": d.get("management", {}).get("name"),
                    })
                return {"companies": results}
    except Exception as e:
        return {"error": str(e)}


async def search_phone(phone: str) -> dict:
    key = config.get("DADATA_API_KEY", "")
    if not key:
        return {"error": "DADATA_API_KEY not set"}
    url = "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/phone"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Token {key}",
    }
    payload = {"query": phone}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=15) as resp:
                if resp.status != 200:
                    return {"error": f"HTTP {resp.status}"}
                data = await resp.json()
                if data.get("suggestions"):
                    s = data["suggestions"][0]
                    return {
                        "phone": s.get("value"),
                        "operator": s.get("data", {}).get("provider"),
                        "region": s.get("data", {}).get("region"),
                        "city": s.get("data", {}).get("city"),
                    }
                return {"found": False}
    except Exception as e:
        return {"error": str(e)}