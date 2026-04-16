import logging
from typing import Optional
import asyncio

from base_fetcher import BaseFetcher

URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
logging.basicConfig(level=logging.INFO)

class VanillaFetcher(BaseFetcher):
    platform_id = 'vanilla'
    platform_name = "Vanilla"
    platform_uid = 'net.minecraft'

    async def fetch(self) -> Optional[dict]:
        data = await self.get_json(URL)
        if not data:
            return None
        
        versions = []
        async def fetch_one(v: dict) -> Optional[dict]:
            ver_data = await self.get_json(v["url"])
            if not ver_data:
                return None
        
            downloads = ver_data.get("downloads", {})
            if "server" not in downloads:
                return None
        
            server = downloads["server"]
            logging.info(f"Fetched {v["id"]} Minecraft version(Vanilla)")
            return {
                "mcVersion": v["id"],
                "builds": [
                    {
                        "build": None,
                        "type": v["type"],
                        "releaseTime": v["releaseTime"],
                        "recommended": v["type"] == "release",
                        "download": {
                            "name": f"minecraft_server.{v['id']}.jar",
                            "url": server["url"],
                            "sha1": server["sha1"]
                        }
                    }
                ]
            }

        tasks = [fetch_one(v) for v in data["versions"]]
        results = await asyncio.gather(*tasks)
        for entry in results:
            if entry:
                versions.append(entry)
        
        logging.info('Added Minecraft versions to JSON(Vanilla)')
        return {
            "platform": "vanilla",
            "name": "Vanilla",
            "uid": self.platform_uid,
            "versions": versions
        }