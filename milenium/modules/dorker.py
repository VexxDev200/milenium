import requests

SERPER_API_KEY = "aa5e4493cf512ca03e544aaef8fd1f90538eda2e"  # вставь свой
SERPER_URL = "https://google.serper.dev/search"

def dork(query, num=10):
    """
    Выполняет Google Dork через Serper API.
    Возвращает список ссылок.
    """
    if not SERPER_API_KEY or SERPER_API_KEY == "YOUR_SERPER_KEY":
        return []

    payload = {"q": query, "num": num}
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json",
    }
    try:
        r = requests.post(SERPER_URL, json=payload, headers=headers, timeout=15)
        data = r.json()
        return [item["link"] for item in data.get("organic", [])]
    except Exception:
        return []

def search_nick(nick, num=10):
    """Ищет ник через Google с разными операторами."""
    queries = [
        f'"{nick}"',
        f'"{nick}" site:github.com',
        f'"{nick}" site:twitter.com',
        f'"{nick}" site:reddit.com',
        f'"{nick}" site:instagram.com',
        f'"{nick}" inurl:profile',
        f'"{nick}" filetype:pdf',
        f'"{nick}" site:pastebin.com',
        f'"{nick}" site:linkedin.com',
    ]
    results = {}
    for q in queries:
        links = dork(q, num)
        if links:
            results[q] = links
    return results