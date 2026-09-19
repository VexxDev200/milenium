import requests
from milenium.modules.permutator import generate

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
    "keybase": "https://keybase.io/{}",
    "hackerone": "https://hackerone.com/{}",
    "bugcrowd": "https://bugcrowd.com/{}",
}

HEADERS = {"User-Agent": "Mozilla/5.0"}

def check_one(nick):
    """Проверяет один ник по всем сайтам."""
    out = {}
    for site, url in SITES.items():
        full = url.format(nick)
        try:
            r = requests.get(full, headers=HEADERS, timeout=8, allow_redirects=True)
            out[site] = {"found": r.status_code == 200, "url": full}
        except Exception:
            out[site] = {"found": False, "url": full}
    return out

def check(nick, permutations=30):
    """
    Проверяет ник и все его вариации.
    Возвращает {ник: {сайт: {found, url}}}
    """
    variants = generate(nick, limit=permutations)
    all_results = {}
    for v in variants:
        all_results[v] = check_one(v)
    return all_results