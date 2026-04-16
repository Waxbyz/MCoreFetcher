import asyncio
import logging
from datetime import datetime, timezone

URL = "https://api.purpurmc.org/v2/purpur/"
from base_fetcher import BaseFetcher

logging.basicConfig(level=logging.INFO)

class PurpurFetcher(BaseFetcher):
    platform_id = "purpur"
    platform_name = "Purpur"
    platform_uid = "build.purpurmc.purpur"

    async def fetch(self) -> dict:
        data = await self.get_json(URL)
        if not data:
            return None
        
        versions = list(reversed(data.get('versions', [])))

        async def fetch_one(version) -> dict:
            builds = await self._fetch_builds(version)
            if not builds:
                return None

            return {
                "version": version,
                "builds": builds
            }

        tasks = [fetch_one(v) for v in versions]
        results = await asyncio.gather(*tasks)

        versions_data = [r for r in results if r]

        return {
            "platform": self.platform_id,
            "name": self.platform_name,
            "uid": self.platform_uid,
            "versions": versions_data
        }
        
    async def _fetch_builds(self, version: str):
        data = await self.get_json(f"{URL}{version}")
        if not data:
            return []

        builds = []

        async def fetch_one_build(b):
            info = await self.get_json(f"{URL}{version}/{b}")
            if not info:
                return None

            ts = info.get("timestamp")
            release_time = ""
            if ts:
                release_time = datetime.fromtimestamp(ts / 1000, timezone.utc).isoformat()

            return {
                "build": str(b),
                "type": "default",
                "releaseTime": release_time,
                "recommended": False,
                "download": {
                    "name": f"purpur-{version}-{b}.jar",
                    "url": f"{URL}{version}/{b}/download",
                    "md5": info.get("md5", "")
                }
            }

        tasks = [fetch_one_build(b) for b in data.get("builds", {}).get("all", [])]
        results = await asyncio.gather(*tasks)

        builds = [r for r in results if r]

        builds.sort(key=lambda b: int(b["build"]), reverse=True)

        if builds:
            builds[0]["recommended"] = True

        return builds