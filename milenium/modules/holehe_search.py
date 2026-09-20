import asyncio


async def check(email: str) -> dict:
    try:
        proc = await asyncio.create_subprocess_exec(
            "holehe", email, "--only-used", "--no-color",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        lines = stdout.decode("utf-8", errors="ignore").splitlines()
        found = [l for l in lines if "[+]" in l]
        return {"found": len(found), "sites": found[:100]}
    except Exception as e:
        return {"error": str(e)}