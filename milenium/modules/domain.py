import whois
import dns.resolver
import requests

def check(host):
    out = {}
    try:
        w = whois.whois(host)
        out["registrar"] = w.registrar
        out["creation"] = str(w.creation_date)
        out["expiration"] = str(w.expiration_date)
        out["name_servers"] = w.name_servers
    except Exception as e:
        out["whois_error"] = str(e)

    for rtype in ["A", "MX", "NS", "TXT"]:
        try:
            out[rtype] = [str(r) for r in dns.resolver.resolve(host, rtype)]
        except Exception:
            out[rtype] = []

    try:
        r = requests.get(f"https://crt.sh/?q=%25.{host}&output=json", timeout=10)
        out["crt_subdomains"] = list({e["name_value"] for e in r.json()})
    except Exception:
        out["crt_subdomains"] = []
    return out