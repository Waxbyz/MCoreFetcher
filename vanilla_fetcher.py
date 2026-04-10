import logging
from typing import Optional
import asyncio

from base_fetcher import BaseFetcher

URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"

class VanillaFetcher(BaseFetcher):
    platform_id = 'vanilla'
    platform_name = "Vanilla"
    platform_uid = 'net.minecraft'

    async def fetch_mc_versions(self) -> list[str]:
        data = await self.get_json(URL)
        if not data:
            return []
        versions = [v['id'] for v in data['versions']]
        logging.info(f'Fetched Minecraft {len(versions)} versions(Vanilla)')

        return versions

    async def fetch_builds(self) -> list:
        logging.warning('Vanilla does not support builds')
        return []
    
    async def fetch_all_versions(self) -> Optional[dict]:
        data = await self.get_json(URL)
        if not data:
            return None
        
        versions = []

        import asyncio
        tasks = [self._fetch_one_version(v) for v in data["versions"]]
        results = await asyncio.gather(*tasks)
        for entry in results:
            if entry:
                versions.append(entry)
        
        logging.info('Added Minecraft versions to JSON(Vanilla)')
        return {
            "formatVersion": 1,
            "platform":      "vanilla",
            "uid":           self.platform_uid,
            "versions":      versions
        }

    async def _fetch_one_version(self, v: dict) -> Optional[dict]:
        ver_data = await self.get_json(v["url"])
        if not ver_data:
            return None
        
        downloads = ver_data.get("downloads", {})
        if "server" not in downloads:
            return None
        
        server = downloads["server"]
        return {
            "mcVersion":   v["id"],
            "type":        v["type"],
            "releaseTime": v["releaseTime"],
            "recommended": v["type"] == "release",
            "download": {
                "name": f"minecraft_server.{v['id']}.jar",
                "url":  server["url"],
                "sha1": server["sha1"]
            }
        }
    
async def main():
    fetcher = VanillaFetcher()
    try:
        versions = await fetcher.fetch_all_versions()
        print(versions)
    finally:
        await fetcher.close()

if __name__ == "__main__":
    asyncio.run(main())