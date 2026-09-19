import requests
from bs4 import BeautifulSoup

def check_channel(username):
    """Парсит публичную страницу t.me/<username> без API."""
    try:
        r = requests.get(f"https://t.me/{username}", timeout=10)
        if r.status_code != 200:
            return {"error": f"HTTP {r.status_code}"}
        soup = BeautifulSoup(r.text, "html.parser")
        title = soup.find("meta", property="og:title")
        desc = soup.find("meta", property="og:description")
        return {
            "exists": True,
            "title": title["content"] if title else None,
            "description": desc["content"] if desc else None,
            "url": f"https://t.me/{username}",
        }
    except Exception as e:
        return {"error": str(e)}