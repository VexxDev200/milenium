import requests
import re

def check(username):
    """Парсит публичный профиль Instagram без API (может ломаться при защите)."""
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(f"https://www.instagram.com/{username}/", headers=headers, timeout=15)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}"}
        m = re.search(r'"edge_followed_by":\{"count":(\d+)\}', r.text)
        followers = m.group(1) if m else None
        m2 = re.search(r'"edge_follow":\{"count":(\d+)\}', r.text)
        following = m2.group(1) if m2 else None
        m3 = re.search(r'"biography":"(.*?)"', r.text)
        bio = m3.group(1) if m3 else None
        return {
            "exists": True,
            "followers": followers,
            "following": following,
            "bio": bio,
            "url": f"https://instagram.com/{username}",
        }
    except Exception as e:
        return {"error": str(e)}