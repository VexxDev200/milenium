from milenium.modules import (
    pwned_passwords, breach_local, hibp, dehashed, leakcheck,
    email_validator, gravatar, pgp_lookup, github_search,
    wayback, reverse_whois, password_pattern,
    ip_geo_advanced, tg_parser,
)

def run(email=None, username=None, phone=None, password=None, db_path=None, domain=None):
    out = {}

    if password:
        out["pwned_passwords"] = pwned_passwords.check_password(password)

    if email:
        out["hibp"] = hibp.check_email(email)
        out["dehashed_email"] = dehashed.search(f'email:"{email}"')
        out["leakcheck_email"] = leakcheck.search(email)
        out["gravatar"] = gravatar.check(email)
        out["pgp"] = pgp_lookup.check(email)
        out["github_email"] = github_search.check_email(email)
        out["email_valid"] = email_validator.check(email)

    if username:
        out["dehashed_username"] = dehashed.search(f'username:"{username}"')
        out["leakcheck_username"] = leakcheck.search(username)
        out["github_user"] = github_search.check_username(username)
        out["telegram"] = tg_parser.channel_info(username)

    if phone:
        out["leakcheck_phone"] = leakcheck.search(phone)

    if domain:
        out["wayback"] = wayback.check(f"http://{domain}")
        out["reverse_whois"] = reverse_whois.check(domain)

    if db_path:
        q = email or username or phone
        if q:
            out["breach_local"] = breach_local.search(q, db_path)

    return out