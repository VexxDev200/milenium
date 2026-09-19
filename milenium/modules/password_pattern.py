import itertools
from datetime import datetime

def generate(name=None, surname=None, birth_year=None, nick=None, limit=500):
    """Генерит вероятные пароли по данным жертвы."""
    base = []
    if name: base.append(name.lower())
    if surname: base.append(surname.lower())
    if nick: base.append(nick.lower())
    if name and surname:
        base.append(f"{name.lower()}{surname.lower()}")
        base.append(f"{name.lower()}.{surname.lower()}")
        base.append(f"{name.lower()}_{surname.lower()}")

    suffixes = ["", "123", "1234", "12345", "2024", "2025", "!", "@", "#", "_"]
    if birth_year:
        suffixes += [str(birth_year), str(birth_year)[-2:], f"{birth_year}!"]

    out = set()
    for b in base:
        for s in suffixes:
            out.add(b + s)
            out.add(b.capitalize() + s)
            out.add(b.upper() + s)

    # leet
    leet_map = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5"}
    for b in list(out)[:100]:
        leet = "".join(leet_map.get(c, c) for c in b)
        out.add(leet)

    return {"passwords": list(out)[:limit], "count": len(out)}