import json
import os
from datetime import datetime

def save(data, name="report"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{ts}.json"
    path = os.path.abspath(filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"ts": ts, "data": data}, f, indent=2, ensure_ascii=False)
    return path

def save_text(lines, name="report"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{name}_{ts}.txt"
    path = os.path.abspath(filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path