import requests

def check_ip(ip):
    """Публичная информация об IP через Shodan InternetDB (без ключа)."""
    try:
        r = requests.get(f"https://internetdb.shodan.io/{ip}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            return {
                "ports": data.get("ports", []),
                "hostnames": data.get("hostnames", []),
                "cpes": data.get("cpes", []),
                "vulns": data.get("vulns", []),
                "tags": data.get("tags", []),
            }
        return {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}