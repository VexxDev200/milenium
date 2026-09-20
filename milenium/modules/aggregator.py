import asyncio
from milenium.modules import (
    shodan_search, censys_search, virustotal_search,
    abuseipdb_search, ipinfo_search, urlscan_search,
    maigret_search, sherlock_search, holehe_search,
)


async def run_async(email=None, username=None, phone=None, ip=None, url=None):
    tasks = {}

    if ip:
        tasks["shodan"] = shodan_search.check_ip(ip)
        tasks["censys"] = censys_search.check_host(ip)
        tasks["virustotal"] = virustotal_search.check_ip(ip)
        tasks["abuseipdb"] = abuseipdb_search.check(ip)
        tasks["ipinfo"] = ipinfo_search.check(ip)

    if username:
        tasks["maigret"] = maigret_search.check(username)
        tasks["sherlock"] = sherlock_search.check(username)

    if email:
        tasks["holehe"] = holehe_search.check(email)
        tasks["virustotal_domain"] = virustotal_search.check_domain(email.split("@")[-1])

    if url:
        tasks["urlscan"] = urlscan_search.check(url)

    results = {}
    if tasks:
        keys = list(tasks.keys())
        values = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for k, v in zip(keys, values):
            if isinstance(v, Exception):
                results[k] = {"error": str(v)}
            else:
                results[k] = v
    return results


def run(**kwargs):
    return asyncio.run(run_async(**kwargs))