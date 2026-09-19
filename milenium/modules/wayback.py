import requests

def check(url):
    try:
        r = requests.get(
            "http://archive.org/wayback/available",
            params={"url": url},
            timeout=15,
        )
        if r.status_code == 200:
            data = r.json()
            snap = data.get("archived_snapshots", {}).get("closest")
            if snap:
                return {"available": True, "snapshot": snap["url"], "timestamp": snap["timestamp"]}
            return {"available": False}
        return {"error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"error": str(e)}