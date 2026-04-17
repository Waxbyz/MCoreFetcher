import asyncio
import json
import logging
import os

from vanilla_fetcher import VanillaFetcher
from paper_fetcher import PaperFetcher
from purpur_fetcher import PurpurFetcher
from aggregator import aggregate

logging.basicConfig(level=logging.INFO)

async def main():
    fetchers = [VanillaFetcher(), PaperFetcher(), PurpurFetcher()]
    os.makedirs("dist", exist_ok=True)

    try:
        data = await aggregate(fetchers)

        with open("dist/meta.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

            logging.info("meta.json generated successfully")
    finally:
        await asyncio.gather(*[f.close() for f in fetchers])


if __name__ == "__main__":
    asyncio.run(main())