import asyncio
import json


async def check(username: str) -> dict:
    """Maigret: поиск по 3000+ сайтам."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "maigret", username, "--json", "simple", "--no-progressbar",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        data = json.loads(stdout.decode("utf-8", errors="ignore"))
        found = [k for k, v in data.items() if v.get("status") == "claimed"]
        return {"found": len(found), "sites": found[:100]}
    except Exception as e:
        return {"error": str(e)}