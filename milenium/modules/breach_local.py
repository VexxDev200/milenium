import os
import re

def search(query, db_path):
    """
    Ищет query (email, username, домен) в локальной базе BreachCompilation.
    db_path — путь к папке с распакованными файлами дампа.
    """
    results = []
    if not os.path.isdir(db_path):
        return {"error": f"path not found: {db_path}"}

    pattern = re.compile(re.escape(query), re.IGNORECASE)
    for root, _, files in os.walk(db_path):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if pattern.search(line):
                            results.append(line.strip())
                            if len(results) >= 1000:
                                return {"matches": results, "truncated": True}
            except Exception:
                continue
    return {"matches": results, "truncated": False}