import requests

def check_email(email):
    try:
        r = requests.get(
            f"https://api.github.com/search/users?q={email}+in:email",
            headers={"Accept": "application/vnd.github+json"},
            timeout=10,
        )
        if r.status_code == 200:
            items = r.json().get("items", [])
            return {"users": [{"login": u["login"], "url": u["html_url"]} for u in items]}
        return {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def check_username(username):
    try:
        r = requests.get(
            f"https://api.github.com/search/users?q={username}+in:login",
            headers={"Accept": "application/vnd.github+json"},
            timeout=10,
        )
        if r.status_code == 200:
            items = r.json().get("items", [])
            return {"users": [{"login": u["login"], "url": u["html_url"]} for u in items]}
        return {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}