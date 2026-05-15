import logging
from typing import Optional

from meta.run.base_fetcher import BaseFetcher
from meta.models.java_model import (
    MojangJavaRuntime,
    JavaBuild,
    JavaVersionFile,
    JavaVersionEntry,
    JavaMetaPackage
)

ADOPTIUM_API = "https://api.adoptium.net/v3/assets/latest/{major}/hotspot"
MOJANG_JAVA_URL = ("https://piston-meta.mojang.com/v1/products/java-runtime/2ec0cc96c44e5a76b9c8b7c39df7210883d12871/all.json")

JAVA_MAJORS = [8, 17, 21, 25]

MOJANG_COMPONENTS = {
    "jre-legacy": 8,
    "java-runtime-alpha": 16,
    "java-runtime-beta": 17,
    "java-runtime-gamma": 17,
    "java-runtime-gamma-snapshot": 17,
    "java-runtime-delta": 21,
    "java-runtime-epsilon": 25
}
MOJANG_OS_MAP = {
    "linux": "linux-x64",
    "linux-i386": "linux-x86",
    "mac-os": "mac-x64",
    "mac-os-arm64": "mac-aarch64",
    "windows-x64": "windows-x64",
    "windows-x86": "windows-x86",
    "windows-arm64": "windows-arm64",
}

ADOPTIUM_PLATFORM_MAP = {
    ("linux", "x64"): "linux-x64",
    ("linux", "aarch64"): "linux-aarch64",
    ("linux", "x86"): "linux-x86",
    ("alpine-linux", "x64"): "linux-alpine-x64",
    ("windows", "x64"): "windows-x64",
    ("windows", "x86"): "windows-x86",
    ("windows", "aarch64"): "windows-arm64",
    ("mac", "x64"): "mac-x64",
    ("mac", "aarch64"): "mac-aarch64",
}

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class MojangJavaFetcher(BaseFetcher):
    platform_id = "java"
    platform_name = "Java Runtimes"
    platform_uid = "net.minecraft.java"

    async def fetch(self) -> Optional[tuple[JavaMetaPackage, dict[str, JavaVersionFile]]]:
        logger.info("[MojangJava] Fetching Java index...")

        raw = await self.get_json(MOJANG_JAVA_URL)
        if not raw:
            return None
        
        builds_by_major: dict[int, dict[str, list[JavaBuild]]] = {}
        for mojang_os, our_platform in MOJANG_OS_MAP.items():
            os_component = raw.get(mojang_os, {})

            for component, major in MOJANG_COMPONENTS.items():
                runtime_list = os_component.get(component, [])
                if not runtime_list:
                    continue
                
                runtime = MojangJavaRuntime(**runtime_list[0])

                java_build = JavaBuild.from_mojang(runtime, recommended=False, component=component, major=major)

                if major not in builds_by_major:
                    builds_by_major[major] = {}

                if our_platform not in builds_by_major[major]:
                    builds_by_major[major][our_platform] = []

                builds_by_major[major][our_platform].append(java_build)
            
            for _, platform_builds in builds_by_major.items():
                for _, builds in platform_builds.items():
                    builds[0].recommended = True
            
            version_files: dict[str, JavaVersionFile] = {}
            version_entries: list[JavaVersionEntry] = []

            for major, platforms in sorted(builds_by_major.items()):
                key = f"java-{major}"

                version_file = JavaVersionFile(
                    uid=key,
                    major=major,
                    platforms=platforms
                )

                version_files[key] = version_file

                version_entries.append(JavaVersionEntry(
                    java_version=key,
                    sha256="",
                    url=f"{self.platform_uid}/{key}.json",
                    major=major
                ))

                total_builds = sum(len(b) for b in platforms.values())
                logger.info(f"[MojangJava] Java {major} — {len(platforms)} platforms, {total_builds} builds")

        meta_package = JavaMetaPackage(
            uid=self.platform_uid,
            name=self.platform_name,
            recommended=[],
            versions=version_entries
        )

        logger.info(f"[MojangJava] Done — {len(version_files)} Java versions")
        return meta_package, version_files   