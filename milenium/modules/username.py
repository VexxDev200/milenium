import requests

SITES = {
    "github": "https://github.com/{}",
    "twitter": "https://twitter.com/{}",
    "instagram": "https://instagram.com/{}",
    "reddit": "https://reddit.com/user/{}",
    "telegram": "https://t.me/{}",
    "tiktok": "https://tiktok.com/@{}",
    "youtube": "https://youtube.com/@{}",
    "vk": "https://vk.com/{}",
    "facebook": "https://facebook.com/{}",
    "twitch": "https://twitch.tv/{}",
    "steam": "https://steamcommunity.com/id/{}",
    "pinterest": "https://pinterest.com/{}",
    "medium": "https://medium.com/@{}",
    "habr": "https://habr.com/ru/users/{}/",
}

HEADERS = {"User-Agent": "Mozilla/5.0"}

def check(nick):
    out = {}
    for site, url in SITES.items():
        try:
            r = requests.get(url.format(nick), headers=HEADERS, timeout=8, allow_redirects=True)
            out[site] = r.status_code == 200
        except Exception:
            out[site] = False
    return out