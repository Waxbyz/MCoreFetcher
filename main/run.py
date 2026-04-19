import asyncio
import json
import logging
import os

from vanilla_fetcher import VanillaFetcher
from paper_fetcher import PaperFetcher
from purpur_fetcher import PurpurFetcher
from fabric_fetcher import FabricFetcher
from aggregator import aggregate

logging.basicConfig(level=logging.INFO)

async def main():
    fetchers = [VanillaFetcher(), PaperFetcher(), PurpurFetcher(), FabricFetcher()]
    os.makedirs("dist", exist_ok=True)

    try:
        data = await aggregate(fetchers)

        for platform in data["platforms"]:
            if not platform:
                continue
            platform_id = platform["platform"]
            platform_file = f"dist/{platform_id}_meta.json"
            with open(platform_file, "w", encoding="utf-8") as f:
                json.dump(platform, f, indent=2)
                logging.info(f"{platform_id}_meta.json generated successfully")
    finally:
        await asyncio.gather(*[f.close() for f in fetchers])


if __name__ == "__main__":
    asyncio.run(main())