import logging
import asyncio

from meta.run.base_fetcher import BaseFetcher

URL = "https://meta.fabricmc.net/v2/versions"
logging.basicConfig(level=logging.INFO)


class FabricFetcher(BaseFetcher):
    platform_id = "fabric"
    platform_name = "Fabric"
    platform_uid = "net.fabricmc"

    async def fetch(self) -> dict:
        data = await self.get_json(f"{URL}/game")
        if not data:
            return None

        versions = [v["version"] for v in data]

        installer_version = await self._fetch_installer_version()

        async def fetch_one(version) -> dict:
            builds = await self._fetch_builds(version, installer_version)
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

    async def _fetch_builds(self, version: str, installer_version: str) -> list[dict]:
        data = await self.get_json(f"{URL}/loader/{version}")
        if not data:
            return []

        builds = []

        for entry in data:
            loader = entry.get("loader", {})
            loader_version = loader.get("version")

            if not loader_version:
                continue

            builds.append({
                "build": loader_version,
                "type": "stable" if loader.get("stable") else "snapshot",
                "releaseTime": "",
                "recommended": loader.get("stable", False),
                "download": {
                    "name": f"fabric-{version}-{loader_version}.jar",
                    "url": f"{URL}/loader/{version}/{loader_version}/{installer_version}/server/jar",
                    "sha1": ""
                }
            })

        for b in builds:
            if b["type"] == "stable":
                b["recommended"] = True
                break

        logging.info(f"Found {len(builds)} builds (Fabric {version})")
        return builds

    async def _fetch_installer_version(self) -> str:
        data = await self.get_json(f"{URL}/installer")
        if not data:
            return None

        for v in data:
            if v.get("stable"):
                return v["version"]

        return data[0]["version"]