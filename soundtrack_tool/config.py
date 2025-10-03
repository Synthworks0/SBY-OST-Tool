from __future__ import annotations
import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
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

def _load_runtime_config() -> dict:
    import sys
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
        config_candidates = [
            base_path / 'runtime_config.json',
            base_path / '_internal' / 'runtime_config.json',
        ]
    else:
        config_candidates = [Path('runtime_config.json')]
    
    for config_path in config_candidates:
        if config_path.exists():
            try:
                return json.loads(config_path.read_text())
            except Exception:
                pass
    return {}

def load_app_config() -> AppConfig:
    runtime_config = _load_runtime_config()
    
    mode_str = runtime_config.get("asset_mode") or _get_env("SBY_ASSET_MODE", "auto") or "auto"
    mode = AssetMode(mode_str.lower())
    
    base_url = runtime_config.get("r2_base_url") or _get_env("SBY_R2_BASE_URL")
    prefix = runtime_config.get("r2_prefix") or _get_env("SBY_R2_PREFIX", DEFAULT_PREFIX) or ""
    prefix = prefix.strip().strip("/")

    r2_enabled = bool(base_url)
    r2_settings = R2Settings(
        enabled=r2_enabled,
        base_url=base_url,
        prefix=prefix,
    )
    return AppConfig(asset_mode=mode, r2=r2_settings)


__all__ = ["AssetMode", "AppConfig", "R2Settings", "load_app_config"]
