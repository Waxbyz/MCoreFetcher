import logging
import asyncio

from base_fetcher import BaseFetcher

URL = "https://api.papermc.io/v2/projects/paper"

class PaperFetcher(BaseFetcher):
    platform_id = "paper"
    platform_name = "Paper"
    platform_uid = "io.papermc.paper"

    async def fetch(self) -> list[str]:
        data = await self.get_json(URL)
        if not data:
            return None
        
        versions = list(reversed(data.get('versions', [])))

        async def fetch_one(version):
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
    
    async def _fetch_builds(self, version: str) -> list[int]:
        data = await self.get_json(f"{URL}/versions/{version}/builds")
        if not data:
            return []

        builds = []
        for b in data.get("builds", []):
            app = b.get('downloads', {}).get('application')
            if not app:
                continue
            
            jar_name = app["name"]
            build = b["build"]
            channel = b.get('channel', 'default')

            builds.append({
            "build": str(build),
            "type": channel,
            "releaseTime": b.get('time', ''),
            "recommended": False,
            "download": {
                "name": jar_name,
                "url": f"{URL}/versions/{version}/builds/{build}",
                "sha1": app.get('sha256', '')
            }
        })
        
        builds.sort(key=lambda b: int(b["build"]), reverse=True)

        for b in builds:
            if b['type'] == 'STABLE':
                b['recommended'] = True
                break

        logging.info(f"Found {len(builds)} builds(Paper)")
        return builds