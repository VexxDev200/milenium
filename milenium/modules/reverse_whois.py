import requests
from bs4 import BeautifulSoup

def check(query):
    """Парсит viewdns.info — бесплатно, без API-ключа."""
    try:
        r = requests.get(
            "https://viewdns.info/reversewhois/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=20,
        )
        soup = BeautifulSoup(r.text, "html.parser")
        table = soup.find("table", {"border": "1"})
        if not table:
            return {"domains": []}
        domains = []
        for row in table.find_all("tr")[1:]:
            cols = row.find_all("td")
            if cols:
                domains.append(cols[0].text.strip())
        return {"domains": domains[:100]}
    except Exception as e:
        return {"error": str(e)}