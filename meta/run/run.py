import asyncio
import json
import logging
from datetime import datetime, timezone
import os
from pathlib import Path

from meta.run.mojang_fetcher import MojangFetcher
from meta.models import MetaIndex, MetaIndexEntry
from meta.common import sha256, write_json

logging.basicConfig(level=logging.INFO)

async def main():
    fetchers = [MojangFetcher()]
    os.makedirs("dist", exist_ok=True)
    output = Path("dist")

    try:
        results = await asyncio.gather(*[f.fetch() for f in fetchers])

        platform_entries = []
        
        for fetcher, result in zip(fetchers, results):
            if not result:
                continue
            package, versions_files = result
            uid = fetcher.platform_uid
            platform_dir = output / uid

            for mc_version, version_file in versions_files.items():
                version_json = version_file.model_dump(by_alias=True)
                version_str = json.dumps(version_json)

                for entry in package.versions:
                    if entry.mc_version == mc_version:
                        entry.sha256 = sha256(version_str)
                        break
                
                write_json(platform_dir / f"{mc_version}.json", version_json)

            package_json = package.model_dump(by_alias=True)
            package_str = json.dumps(package_json)
            write_json(platform_dir / "package.json", package_json)

            platform_entries.append(MetaIndexEntry(
                uid=uid,
                name=fetcher.platform_name,
                sha256=sha256(package_str),
                url=f"{uid}/package.json"
            ))
        
        index = MetaIndex(
            generatedAt=datetime.now(timezone.utc).isoformat(),
            platforms=platform_entries
        )
        write_json(output / "index.json", index.model_dump(by_alias=True))


    finally:
        await asyncio.gather(*[f.close() for f in fetchers])

if __name__ == "__main__":
    asyncio.run(main())