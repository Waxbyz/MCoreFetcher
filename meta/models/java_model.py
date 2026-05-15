from pydantic import BaseModel, Field
from typing import Optional

from . import MetaPackage

#Adoptium
class AdoptiumPackage(BaseModel):
    checksum: Optional[str] = None
    link: str
    name: str
    size: int

    model_config = {"extra": "ignore"}

class AdoptiumBinary(BaseModel):
    architecture: str
    image_type: str
    os: str
    package: AdoptiumPackage
    updated_at: str

    model_config = {"extra": "ignore"}

class AdoptiumVersion(BaseModel):
    build: int
    major: int
    minor: int
    security: int
    openjdk_version: str

    model_config = {"extra": "ignore"}

class AdoptiumEntry(BaseModel):
    binary: AdoptiumBinary
    release_name: str
    vendor: str
    version: AdoptiumVersion

    model_config = {"extra": "ignore"}

#Mojang
class MojangJavaManifest(BaseModel):
    sha1: str
    size: int
    url: str

    model_config = {"extra": "ignore"}

class MojangJavaVersion(BaseModel):
    name: str
    released: str

    model_config = {"extra": "ignore"}

class MojangJavaRuntime(BaseModel):
    manifest: MojangJavaManifest
    version: MojangJavaVersion

    model_config = {"extra": "ignore"}

#Meta
class JavaChecksum(BaseModel):
    hash: str
    type: str

class JavaVersionInfo(BaseModel):
    build: int
    major: int
    minor: int
    security: int

class JavaBuild(BaseModel):
    checksum: Optional[JavaChecksum] = None    
    download_type: str = Field(alias="downloadType")
    name: str
    release_time: Optional[str] = Field(None, alias="releaseTime")
    release_name: str = Field(alias="releaseName")
    recommended: bool = False
    package_type: str = Field("jre", alias="packageType")
    url: str
    vendor: str
    version_info: JavaVersionInfo

    model_config = {"populate_by_name": True}

    @classmethod
    def from_adoptium(cls, entry: AdoptiumEntry, recommended: bool) -> "JavaBuild":
        v = entry.version

        name = f"eclipse_temurin_jre{v.major}.{v.minor}.{v.security}+{v.build}"

        checksum = None
        if entry.binary.package.checksum:
            checksum = JavaChecksum(
                hash=entry.binary.package.checksum,
                type="sha256"
            )
        
        return cls(
            checksum=checksum,            
            download_type="archive",
            name=name,
            release_time=entry.binary.updated_at,
            release_name=entry.release_name,
            recommended=recommended,
            package_type="jre",
            url=entry.binary.package.link,
            vendor=entry.vendor,
            version_info=JavaVersionInfo(
                build=v.build,
                major=v.major,
                minor=v.minor,
                security=v.security
            )
        )
    
    @classmethod
    def from_mojang(cls, runtime: MojangJavaRuntime, recommended: bool, component: str, major: int) -> "JavaBuild":
        v = runtime.version

        parts = v.name.split(".")
        minor = int(parts[1]) if len(parts) > 1 else 0
        security = int(parts[2]) if len(parts) > 2 else 0

        return cls(
            checksum=JavaChecksum(
                hash=runtime.manifest.sha1,
                type="sha1"
            ),
            download_type="manifest",
            name=component,
            release_time=v.released,
            release_name=v.name,
            recommended=recommended,
            package_type="jre",
            url=runtime.manifest.url,
            vendor="Mojang",
            version_info=JavaVersionInfo(
                build=0,
                major=major,
                minor=minor,
                security=security
            )
        )
    
class JavaVersionFile(BaseModel):
    format_version: int = Field(1, alias="formatVersion")
    uid: str
    major: int
    platforms: dict[str, list[JavaBuild]]

    @classmethod
    def from_runtimes(cls, major: int, uid: str, platforms: dict[str, list[JavaBuild]]) -> "JavaVersionFile":
        index = cls(
            uid=uid,
            major=major,
            platforms=dict)

class JavaVersionEntry(BaseModel):
    java_version: str = Field(alias="javaVersion")
    sha256: str
    url: str
    major: int

    model_config = {"populate_by_name": True}

class JavaMetaPackage(MetaPackage):
    versions: list[JavaVersionEntry]