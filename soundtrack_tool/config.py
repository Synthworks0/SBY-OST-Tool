from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional


def _get_env(key: str, default: str | None = None) -> str | None:
    value = os.environ.get(key)
    if value is None:
        return default
    cleaned = value.strip().strip("\"'")
    return cleaned if cleaned else default




class AssetMode(str, Enum):
    AUTO = "auto"
    LOCAL = "local"
    REMOTE = "remote"


@dataclass
class R2Settings:
    enabled: bool
    bucket: Optional[str]
    endpoint_url: Optional[str]
    access_key: Optional[str]
    secret_key: Optional[str]
    prefix: str
    region: Optional[str]
    presign_ttl: int


@dataclass
class AppConfig:
    asset_mode: AssetMode
    r2: R2Settings

    @property
    def use_remote(self) -> bool:
        if self.asset_mode == AssetMode.REMOTE:
            return True
        if self.asset_mode == AssetMode.LOCAL:
            return False
        return self.r2.enabled


DEFAULT_PREFIX = ""
DEFAULT_PRESIGN_TTL = 3600


def load_app_config() -> AppConfig:
    mode = AssetMode((_get_env("SBY_ASSET_MODE", "auto") or "auto").lower())
    bucket = _get_env("SBY_R2_BUCKET")
    endpoint = _get_env("SBY_R2_ENDPOINT")
    access_key = _get_env("SBY_R2_ACCESS_KEY")
    secret_key = _get_env("SBY_R2_SECRET_KEY")
    region = _get_env("SBY_R2_REGION")
    prefix = (_get_env("SBY_R2_PREFIX", DEFAULT_PREFIX) or "").strip().strip("/")
    presign_raw = _get_env("SBY_R2_PRESIGN_TTL", str(DEFAULT_PRESIGN_TTL)) or str(DEFAULT_PRESIGN_TTL)
    try:
        presign_ttl = int(presign_raw)
    except ValueError:
        presign_ttl = DEFAULT_PRESIGN_TTL

    r2_enabled = bool(bucket and endpoint and access_key and secret_key)
    r2_settings = R2Settings(
        enabled=r2_enabled,
        bucket=bucket,
        endpoint_url=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        prefix=prefix,
        region=region,
        presign_ttl=presign_ttl,
    )
    return AppConfig(asset_mode=mode, r2=r2_settings)


__all__ = ["AssetMode", "AppConfig", "R2Settings", "load_app_config"]
