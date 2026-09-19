import smtplib
import dns.resolver

def check(email):
    """Проверка существования email через SMTP RCPT TO (без отправки письма)."""
    domain = email.split("@")[1]
    try:
        mx_records = dns.resolver.resolve(domain, "MX")
        mx_host = str(sorted(mx_records, key=lambda r: r.preference)[0].exchange).rstrip(".")
    except Exception as e:
        return {"error": f"MX lookup failed: {e}"}

    try:
        server = smtplib.SMTP(timeout=10)
        server.connect(mx_host, 25)
        server.helo("milenium.local")
        server.mail("check@milenium.local")
        code, _ = server.rcpt(email)
        server.quit()
        return {"exists": code in (250, 251), "code": code, "mx": mx_host}
    except Exception as e:
        return {"error": str(e), "mx": mx_host}