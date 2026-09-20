import asyncio
import json


async def check(username: str) -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            "sherlock", username, "--json",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        data = json.loads(stdout.decode("utf-8", errors="ignore"))
        return {"found": len(data), "sites": list(data.keys())[:100]}
    except Exception as e:
        return {"error": str(e)}