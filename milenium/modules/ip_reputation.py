import requests

def check(ip):
    out = {}
    try:
        r = requests.get(f"https://ipinfo.io/{ip}/json", timeout=10).json()
        out.update({
            "org": r.get("org"),
            "city": r.get("city"),
            "region": r.get("region"),
            "country": r.get("country"),
            "timezone": r.get("timezone"),
        })
    except Exception as e:
        out["ipinfo_error"] = str(e)

    try:
        r = requests.get(f"https://api.abuseipdb.com/api/v2/check",
                         params={"ipAddress": ip, "maxAgeInDays": 90},
                         headers={"Key": "", "Accept": "application/json"},
                         timeout=10)
        if r.status_code == 200:
            d = r.json().get("data", {})
            out["abuse_score"] = d.get("abuseConfidenceScore")
            out["total_reports"] = d.get("totalReports")
    except Exception:
        pass
    return out