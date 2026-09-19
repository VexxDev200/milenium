import requests

LEAKCHECK_KEY = "97059e7429c29bc190a1e93a97a28c1d6e8d8199"  # ключ с https://leakcheck.io/

def search(term):
    if not LEAKCHECK_KEY:
        return {"error": "no leakcheck key"}
    headers = {"X-API-Key": LEAKCHECK_KEY}
    try:
        r = requests.get(f"https://leakcheck.io/api/v2/query/{term}", headers=headers, timeout=20)
        if r.status_code == 200:
            return r.json()
        else:
            return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}