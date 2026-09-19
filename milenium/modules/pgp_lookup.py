import requests

def check(email):
    try:
        r = requests.get(f"https://keys.openpgp.org/vks/v1/by-email/{email}", timeout=10)
        if r.status_code == 200:
            return {"found": True, "key": r.text[:500]}
        return {"found": False}
    except Exception as e:
        return {"error": str(e)}