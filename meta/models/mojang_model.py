from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from . import MetaDownload, MetaBuild, MetaVersionEntry, MetaPackage, MetaVersionFile

class MojangServerDownload(BaseModel):
    url: str
    sha1: str
    size: int

class MojangDownloads(BaseModel):
    client: Optional[MojangServerDownload] = None
    server: Optional[MojangServerDownload] = None

class MojangJavaVersion(BaseModel):
    component: str
    major_version: int = Field(alias="majorVersion")

    model_config = {"populate_by_name": True}

class MojangManifestEntry(BaseModel):
    id: str
    type: str
    url: str
    release_time: datetime = Field(alias="releaseTime")

    model_config = {"populate_by_name": True}

    @property
    def recommended(self) -> bool:
        return self.type == "release"
    
class MojangManifestLatest(BaseModel):
    release:  str
    snapshot: str

class MojangVersionManifest(BaseModel):
    latest: MojangManifestLatest
    versions: list[MojangManifestEntry]

    def get_version(self, version_id: str) -> Optional[MojangManifestLatest]:
        return next((v for v in self.versions if v.id == version_id), None)
    
class MojangVersion(BaseModel):
    id: str
    type: str
    release_time: Optional[datetime] = Field(None, alias="releaseTime")
    downloads: Optional[MojangDownloads] = None
    java_version: Optional[MojangJavaVersion] = Field(None, alias="javaVersion")
 
    model_config = {"populate_by_name": True}
 
    @property
    def has_server(self) -> bool:
        return self.downloads is not None and self.downloads.server is not None
 
    @property
    def server(self) -> Optional[MojangServerDownload]:
        return self.downloads.server if self.downloads else None
 
    @property
    def required_java_major(self) -> int:
        return self.java_version.major_version if self.java_version else 8
    
class MojangMetaBuild(MetaBuild):
    java_major: int = Field(8, alias="javaMajor")

    model_config = {"populate_by_name": True}

    @classmethod
    def from_mojang(cls, entry: MojangManifestEntry, version: MojangVersion) -> Optional["MojangMetaBuild"]:
        if not version.has_server:
            return None
        
        server = version.server
        return cls(
            build=None,
            type=entry.type,
            releaseTime=entry.release_time.isoformat(),
            recommended=entry.recommended,
            download=MetaDownload(
                name=f"minecraft_server.{entry.id}.jar",
                url=server.url,
                sha1=server.sha1
            ),
            javaMajor=version.required_java_major
        )

class MojangMetaVersionFile(MetaVersionFile):
    builds: list[MojangMetaBuild]

    @classmethod
    def from_manifest_entry(cls, entry: MojangManifestEntry, version: MojangVersion, uid: str) -> Optional["MojangMetaVersionFile"]:
        build = MojangMetaBuild.from_mojang(entry=entry, version=version)
        if not build:
            return None
        
        return cls(
            uid=uid,
            mcVersion=entry.id,
            builds=[build]
        )

class MojangMetaVersionEntry(MetaVersionEntry):
    type: str = "release"

class MojangMetaVersion(MetaPackage):
    versions: list[MojangMetaVersionEntry]