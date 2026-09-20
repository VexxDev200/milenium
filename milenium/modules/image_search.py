import asyncio
from PicImageSearch import Network, Yandex, Google, Bing, Tineye


async def search(image_path: str, engine: str = "yandex") -> dict:
    """PicImageSearch: обратный поиск по фото."""
    engines = {"yandex": Yandex, "google": Google, "bing": Bing, "tineye": Tineye}
    cls = engines.get(engine.lower())
    if not cls:
        return {"error": f"unknown engine: {engine}"}
    try:
        async with Network() as client:
            searcher = cls(client=client)
            resp = await searcher.search(file=image_path)
            results = []
            for item in resp.raw[:10]:
                results.append({
                    "title": getattr(item, "title", None),
                    "url": getattr(item, "url", None),
                    "thumbnail": getattr(item, "thumbnail", None),
                })
            return {"engine": engine, "results": results}
    except Exception as e:
        return {"error": str(e)}