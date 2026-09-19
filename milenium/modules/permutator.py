import itertools

def generate(nick, suffixes=None, leet=True, limit=50):
    """
    Генерит вариации ника:
    - базовый
    - с цифрами (1337, 2024, 0x, 777)
    - с leet-заменами (a->4, e->3, i->1, o->0, s->5)
    - с подчёркиваниями/точками
    - с суффиксами (dev, hack, x, _)
    """
    if suffixes is None:
        suffixes = ["", "1337", "2024", "0x", "777", "x", "dev", "hack", "_", "01", "99", "pro"]

    variants = set()
    variants.add(nick)
    variants.add(nick.lower())
    variants.add(nick.upper())

    # с суффиксами
    for s in suffixes:
        variants.add(f"{nick}{s}")
        variants.add(f"{s}{nick}")

    # с подчёркиваниями/точками
    variants.add(f"_{nick}_")
    variants.add(f"{nick}_")
    variants.add(f"_{nick}")
    variants.add(f"{nick}.{nick}")

    # leet-замены
    if leet:
        leet_map = {"a": "4", "e": "3", "i": "1", "o": "0", "s": "5", "t": "7"}
        leet_nick = "".join(leet_map.get(c.lower(), c) for c in nick)
        variants.add(leet_nick)
        for s in suffixes[:5]:
            variants.add(f"{leet_nick}{s}")

    return list(variants)[:limit]