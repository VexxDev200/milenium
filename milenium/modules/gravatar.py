import hashlib
import requests

def check(email):
    h = hashlib.md5(email.strip().lower().encode()).hexdigest()
    url = f"https://www.gravatar.com/avatar/{h}?d=404"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return {"exists": True, "url": f"https://www.gravatar.com/{h}"}
        return {"exists": False}
    except Exception as e:
        return {"error": str(e)}