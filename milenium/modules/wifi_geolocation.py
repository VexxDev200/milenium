import requests

def check(bssid):
    """Wi-Fi геолокация через wigle.net (нужен API-токен)."""
    try:
        r = requests.get(
            "https://api.wigle.net/api/v2/network/search",
            params={"netid": bssid},
            headers={"Authorization": "Basic YOUR_BASE64_TOKEN"},
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if results:
                first = results[0]
                return {
                    "lat": first.get("trilat"),
                    "lon": first.get("trilong"),
                    "ssid": first.get("ssid"),
                    "country": first.get("country"),
                    "city": first.get("city"),
                }
            return {"found": False}
        return {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}