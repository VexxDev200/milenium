import requests

def check(ip):
    out = {}
    try:
        r = requests.get(f"https://ipapi.co/{ip}/json/", timeout=10).json()
        out["ipapi"] = {k: r.get(k) for k in ["city", "region", "country_name", "org", "asn", "timezone"]}
    except Exception as e:
        out["ipapi_error"] = str(e)

    try:
        r = requests.get(f"https://ipwho.is/{ip}", timeout=10).json()
        out["ipwhois"] = {k: r.get(k) for k in ["city", "region", "country", "connection"]}
    except Exception as e:
        out["ipwhois_error"] = str(e)
    return out