import requests
import socket

def check(address):
    out = {}
    try:
        r = requests.get(f"http://ip-api.com/json/{address}", timeout=8).json()
        out.update({
            "ip": r.get("query"),
            "country": r.get("country"),
            "region": r.get("regionName"),
            "city": r.get("city"),
            "isp": r.get("isp"),
            "org": r.get("org"),
            "as": r.get("as"),
            "lat": r.get("lat"),
            "lon": r.get("lon"),
        })
    except Exception as e:
        out["error"] = str(e)

    try:
        out["reverse_dns"] = socket.gethostbyaddr(address)[0]
    except Exception:
        out["reverse_dns"] = "n/a"
    return out