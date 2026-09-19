import json
from datetime import datetime

def save(data, path="report.json"):
    with open(path, "w") as f:
        json.dump({"ts": datetime.now().isoformat(), "data": data}, f, indent=2)
    return path