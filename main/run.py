import asyncio
import json
import logging

from vanilla_fetcher import VanillaFetcher
from paper_fetcher import PaperFetcher
from aggregator import aggregate

logging.basicConfig(level=logging.INFO)


async def main():
    fetchers = [VanillaFetcher(), PaperFetcher()]

    try:
        data = await aggregate(fetchers)

        with open("meta.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

            logging.info("meta.json generated successfully")
    finally:
        await asyncio.gather(*[f.close() for f in fetchers])


if __name__ == "__main__":
    asyncio.run(main())