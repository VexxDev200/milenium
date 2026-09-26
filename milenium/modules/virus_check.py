import os
import hashlib
import time
from pathlib import Path
from milenium.modules import config, logger


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def check_file_vt(path, max_retries=2):
    """
    Проверяет файл через VirusTotal по SHA256.
    Возвращает dict:
      - clean: bool
      - detections: int
      - total: int
      - permalink: str
      - error: str (если ошибка)
      - skipped: bool (если нет ключа или лимит)
    """
    try:
        from virustotal_python import Virustotal
    except ImportError:
        return {"error": "virustotal_python not installed", "skipped": True}

    api_key = config.get("VIRUSTOTAL_API_KEY", "")
    if not api_key:
        return {"error": "VIRUSTOTAL_API_KEY not set", "skipped": True}

    path = Path(path)
    if not path.exists():
        return {"error": "file not found", "skipped": True}

    file_hash = _sha256(path)

    vtotal = Virustotal(API_KEY=api_key, API_VERSION="v3")

    for attempt in range(max_retries):
        try:
            resp = vtotal.request(f"files/{file_hash}")
            data = resp.data
            attrs = data.get("attributes", {})
            stats = attrs.get("last_analysis_stats", {})
            malicious = stats.get("malicious", 0)
            suspicious = stats.get("suspicious", 0)
            total = sum(stats.values()) if stats else 0
            permalink = f"https://www.virustotal.com/gui/file/{file_hash}"

            # Только чистые угрозы — вирусы/трояны/черви, НЕ PUA, crack, cheat, hacktool
            is_virus = malicious > 0
            return {
                "clean": not is_virus,
                "detections": malicious,
                "suspicious": suspicious,
                "total": total,
                "permalink": permalink,
                "sha256": file_hash,
            }
        except Exception as e:
            err = str(e).lower()
            if "not found" in err or "404" in err:
                # Файл неизвестен VT — можно считать чистым или отправить на скан
                return {
                    "clean": True,
                    "detections": 0,
                    "suspicious": 0,
                    "total": 0,
                    "permalink": f"https://www.virustotal.com/gui/file/{file_hash}",
                    "sha256": file_hash,
                    "not_in_vt": True,
                }
            if "rate" in err or "429" in err:
                logger.progress(f"VT: rate limit, жду 20s")
                time.sleep(20)
                continue
            return {"error": str(e), "skipped": True}

    return {"error": "max retries exceeded", "skipped": True}
