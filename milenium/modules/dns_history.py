import requests

def check(domain):
    try:
        r = requests.get(f"https://crt.sh/?q=%25.{domain}&output=json", timeout=15)
        if r.status_code == 200:
            subs = set()
            for entry in r.json():
                for name in entry.get("name_value", "").split("\n"):
                    subs.add(name.strip())
            return {"subdomains": sorted(subs)}
        return {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}