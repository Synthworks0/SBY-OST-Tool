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
    base_url: Optional[str]
    prefix: str

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

def load_app_config() -> AppConfig:
    mode = AssetMode((_get_env("SBY_ASSET_MODE", "auto") or "auto").lower())
    base_url = _get_env("SBY_R2_BASE_URL")
    prefix = (_get_env("SBY_R2_PREFIX", DEFAULT_PREFIX) or "").strip().strip("/")

    r2_enabled = bool(base_url)
    r2_settings = R2Settings(
        enabled=r2_enabled,
        base_url=base_url,
        prefix=prefix,
    )
    return AppConfig(asset_mode=mode, r2=r2_settings)


__all__ = ["AssetMode", "AppConfig", "R2Settings", "load_app_config"]
