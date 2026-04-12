import logging
from typing import Optional
import asyncio

from base_fetcher import BaseFetcher

URL = "https://api.papermc.io/v2/projects/paper"

class PaperFetcher(BaseFetcher):
    platform_id = "paper"
    platform_name = "Paper"
    platform_uid = "io.papermc.paper"

    async def fetch_mc_verions(self) -> list[str]:
        data = self.get_json(URL)
        if not data:
            return []
        return list(reversed(data.get('versions', [])))
    
    async def fetch_builds(self, version: str) -> list[int]:
        data = self.get_json(f"{URL}/versions/{version}/builds")
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
            "mcVersion": version,
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
            if b['type'] == 'default':
                b['recommended'] == True
                break

        logging.info(f"Found {len(builds)} builds(Paper)")        