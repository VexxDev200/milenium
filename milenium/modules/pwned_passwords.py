import hashlib
import requests

def check_password(password):
    """Проверяет пароль через Pwned Passwords API (k-anonymity). Бесплатно, без ключа."""
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    try:
        r = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=10)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}"}
        for line in r.text.splitlines():
            h, count = line.split(":")
            if h == suffix:
                return {"pwned": True, "count": int(count)}
        return {"pwned": False, "count": 0}
    except Exception as e:
        return {"error": str(e)}