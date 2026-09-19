import requests

def check(query):
    out = {}
    try:
        r = requests.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{query}",
                         headers={"hibp-api-key": "YOUR_KEY"}, timeout=8)
        out["hibp"] = [b["Name"] for b in r.json()] if r.status_code == 200 else []
    except Exception:
        out["hibp"] = "n/a"
    return out