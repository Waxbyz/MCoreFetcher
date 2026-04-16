import asyncio

async def aggregate(fetchers) -> dict:
    platforms = await asyncio.gather(*[f.fetch() for f in fetchers])

    return {
        "formatVersion" : 1,
        "platforms" : platforms
    }