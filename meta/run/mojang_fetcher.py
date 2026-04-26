import logging
from typing import Optional
import asyncio

from meta.run.base_fetcher import BaseFetcher
from meta.models.mojang_model import (
    MojangVersionManifest,
    MojangVersion,
    MojangMetaVersionFile,
    MojangMetaVersionEntry,
    MojangMetaVersion
)

URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class MojangFetcher(BaseFetcher):
    platform_id = "mojang"
    platform_name = "Mojang"
    platform_uid = "net.minecraft"

    async def fetch(self) -> Optional[tuple[MojangMetaVersion, dict[str, MojangMetaVersionFile]]]:
        logger.info("[Mojang] Fetching Mojang manifest...")

        raw_manifest = await self.get_json(URL)
        if not raw_manifest:
            logger.error("[Mojang] Failed to fetch manifest")
            return None

        manifest = MojangVersionManifest(**raw_manifest)
        logger.info(f"[Mojang] Loaded {len(manifest.versions)} versions")

        semaphore = asyncio.Semaphore(10)

        async def fetch_one(entry):
            async with semaphore:
                logger.debug(f"[Mojang] Fetching version: {entry.id}")
                return await self._fetch_version(entry)

        tasks = await asyncio.gather(*[fetch_one(entry) for entry in manifest.versions])

        version_files: dict[str, MojangMetaVersionFile] = {}
        version_entries: list[MojangMetaVersionEntry] = []
        recommended: list[str] = []

        for entry, version_file in zip(manifest.versions, tasks):
            if not version_file:
                logger.debug(f"[Mojang] Skipping {entry.id} (no server)")
                continue

            version_files[entry.id] = version_file

            version_entries.append(
                MojangMetaVersionEntry(
                    mcVersion=entry.id,
                    type=entry.type,
                    sha256="",
                    url=f"{self.platform_uid}/{entry.id}.json",
                )
            )

            recommended = [manifest.latest.release]

        logger.info(f"[Mojang] Processed {len(version_entries)} valid versions")

        package = MojangMetaVersion(
            uid=self.platform_uid,
            name=self.platform_name,
            recommended=recommended,
            versions=version_entries,
        )

        return package, version_files

    async def _fetch_version(self, entry) -> Optional[MojangMetaVersionFile]:
        logger.debug(f"[Mojang] Downloading version data: {entry.id}")

        raw = await self.get_json(entry.url)
        if not raw:
            logger.error(f"[Mojang] Failed to fetch version: {entry.id}")
            return None

        version = MojangVersion(**raw)

        result = MojangMetaVersionFile.from_manifest_entry(
            entry=entry,
            version=version,
            uid=self.platform_uid,
        )

        if result:
            logger.debug(f"[Mojang] Built meta for {entry.id}")
        else:
            logger.debug(f"[Mojang] No server for {entry.id}")

        return result
