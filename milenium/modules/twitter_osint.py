import requests

def check(username):
    """Через nitter-зеркало (может не работать, зеркала меняются)."""
    mirrors = ["https://nitter.net", "https://nitter.privacydev.net"]
    for base in mirrors:
        try:
            r = requests.get(f"{base}/{username}", timeout=10)
            if r.status_code == 200 and "user-profile" in r.text:
                return {"exists": True, "url": f"https://twitter.com/{username}", "mirror": base}
        except Exception:
            continue
    return {"exists": False}