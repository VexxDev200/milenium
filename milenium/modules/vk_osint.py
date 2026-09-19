import requests

def check(user_id, token=""):
    """VK API: нужен сервисный токен. Без него вернёт ошибку."""
    if not token:
        return {"error": "no VK token"}
    try:
        r = requests.get(
            "https://api.vk.com/method/users.get",
            params={
                "user_ids": user_id,
                "fields": "followers_count,country,city,photo_max,bdate",
                "access_token": token,
                "v": "5.199",
            },
            timeout=15,
        )
        data = r.json()
        if "response" in data:
            return data["response"][0]
        return {"error": data.get("error", {}).get("error_msg")}
    except Exception as e:
        return {"error": str(e)}