from milenium.modules import pwned_passwords, breach_local, hibp, dehashed, leakcheck

def run(email=None, username=None, phone=None, password=None, db_path=None):
    out = {}

    if password:
        out["pwned_passwords"] = pwned_passwords.check_password(password)

    if email:
        out["hibp"] = hibp.check_email(email)
        out["dehashed_email"] = dehashed.search(f'email:"{email}"')
        out["leakcheck_email"] = leakcheck.search(email)

    if username:
        out["dehashed_username"] = dehashed.search(f'username:"{username}"')
        out["leakcheck_username"] = leakcheck.search(username)

    if phone:
        out["leakcheck_phone"] = leakcheck.search(phone)

    if db_path:
        q = email or username or phone
        if q:
            out["breach_local"] = breach_local.search(q, db_path)

    return out