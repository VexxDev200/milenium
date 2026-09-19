import subprocess
import os

def check(image_path):
    """Требует exiftool в PATH. Установка: apt install libimage-exiftool-perl / choco install exiftool."""
    if not os.path.exists(image_path):
        return {"error": "file not found"}
    try:
        r = subprocess.run(
            ["exiftool", "-j", image_path],
            capture_output=True, text=True, timeout=20
        )
        if r.returncode != 0:
            return {"error": r.stderr.strip() or "exiftool failed"}
        import json
        data = json.loads(r.stdout)[0]
        keys = ["GPSLatitude", "GPSLongitude", "Model", "Make", "DateTimeOriginal", "Software"]
        return {k: data.get(k) for k in keys if data.get(k)}
    except FileNotFoundError:
        return {"error": "exiftool not installed"}
    except Exception as e:
        return {"error": str(e)}