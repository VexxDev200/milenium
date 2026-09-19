import re
import dns.resolver
import requests

def check(mail):
    out = {}
    if not re.match(r"[^@]+@[^@]+\.[^@]+", mail):
        return {"error": "invalid email"}

    domain = mail.split("@")[1]
    try:
        mx = [str(r.exchange).rstrip(".") for r in dns.resolver.resolve(domain, "MX")]
        out["mx"] = mx
    except Exception:
        out["mx"] = []

    try:
        r = requests.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{mail}",
                         headers={"hibp-api-key": "YOUR_KEY"}, timeout=8)
        if r.status_code == 200:
            out["breaches"] = [b["Name"] for b in r.json()]
        else:
            out["breaches"] = []
    except Exception:
        out["breaches"] = "n/a"

    out["gravatar"] = f"https://www.gravatar.com/avatar/{__import__('hashlib').md5(mail.lower().encode()).hexdigest()}"
    return out