import base64
import requests

DEHASHED_EMAIL = "vexxdev31@gmail.com"  # твой email на dehashed.com
DEHASHED_KEY = "4ASpzd3EjjFo7v2KxFBeHiNzALJTnoKlhDJP46bJ/cthj88W3hyx+roE"    # API key из личного кабинета

def search(query):
    """
    query — например: email:"target@mail.com" или username:"hacker"
    Без подписки вернёт пустой результат или 401.
    """
    if not DEHASHED_EMAIL or not DEHASHED_KEY:
        return {"error": "no dehashed credentials"}

    auth = base64.b64encode(f"{DEHASHED_EMAIL}:{DEHASHED_KEY}".encode()).decode()
    headers = {"Authorization": f"Basic {auth}", "Accept": "application/json"}
    try:
        r = requests.get(
            "https://api.dehashed.com/v2/search",
            params={"query": query, "size": 100},
            headers=headers, timeout=20
        )
        if r.status_code == 200:
            data = r.json()
            return {"entries": data.get("entries", []), "total": data.get("total", 0)}
        else:
            return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}