import requests

HIBP_KEY = ""  # вставь ключ с https://haveibeenpwned.com/API/Key

def check_email(email):
    if not HIBP_KEY:
        return {"error": "no HIBP key configured"}
    headers = {"hibp-api-key": HIBP_KEY, "User-Agent": "milenium"}
    try:
        r = requests.get(
            f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
            headers=headers, timeout=15
        )
        if r.status_code == 200:
            return {"breaches": [b["Name"] for b in r.json()]}
        elif r.status_code == 404:
            return {"breaches": []}
        else:
            return {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}