from __future__ import annotations
import os
import sys
from pathlib import Path

from .environment import (
    get_app_resources_dir,
    get_runtime_root,
    get_user_cache_dir,
    get_user_data_dir,
)


class ResourceLocator:
    def __init__(self, runtime_root: Path | None = None, resources_dir: Path | None = None) -> None:
        self._runtime_root = runtime_root or get_runtime_root()
        self._app_resources_dir = resources_dir or get_app_resources_dir(self._runtime_root)
        self._variant = self._detect_variant()
        self._bundle_identifier = self._determine_bundle_identifier()
        self._app_display_name = self._determine_app_display_name()
        self._user_data_dir = get_user_data_dir(self._app_display_name, self._bundle_identifier)
        self._user_cache_dir = get_user_cache_dir(self._app_display_name, self._bundle_identifier)
        self._user_data_dir.mkdir(parents=True, exist_ok=True)
        self._user_cache_dir.mkdir(parents=True, exist_ok=True)
        self._resources_root = self._detect_resources_root()
        self._soundtrack_root = self._detect_soundtrack_root()
        self._user_settings_path = self._user_data_dir / "config.json"

    @property
    def runtime_root(self) -> Path:
        return self._runtime_root

    @property
    def app_resources_dir(self) -> Path:
        return self._app_resources_dir

    @property
    def resources_root(self) -> Path:
        return self._resources_root

    @property
    def soundtrack_root(self) -> Path:
        return self._soundtrack_root

    @property
    def bundle_identifier(self) -> str:
        return self._bundle_identifier

    @property
    def user_data_dir(self) -> Path:
        return self._user_data_dir

    @property
    def user_cache_dir(self) -> Path:
        return self._user_cache_dir

    @property
    def user_settings_path(self) -> Path:
        return self._user_settings_path

    def main_qml_path(self) -> Path:
        return self.app_resources_dir / "qml" / "main.qml"

    def application_icon_path(self, name: str = "icon.ico") -> Path:
        if sys.platform.startswith("linux"):
            png_name = name.replace(".ico", ".png")
            png_candidates = [
                self.runtime_root / "_internal" / png_name,
                self.app_resources_dir / png_name,
                self.resources_root / png_name,
                self.runtime_root / png_name,
            ]
            for candidate in png_candidates:
                if candidate.exists():
                    return candidate

        candidates = [
            self.runtime_root / "_internal" / name,
            self.app_resources_dir / name,
            self.resources_root / name,
            self.runtime_root / name,
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return candidates[-1]

    def icon_path(self, name: str = "icon.ico") -> Path:
        return self.application_icon_path(name)

    def soundtrack_collection_root(self) -> Path:
        return self._soundtrack_root

    def soundtrack_source_dir(self, english_album_name: str) -> Path:
        return self.soundtrack_collection_root() / english_album_name

    def resource_path(self, *parts: str | Path) -> Path:
        path = self.resources_root
        for part in parts:
            path /= Path(part)
        return path

    def qml_search_candidates(self) -> list[Path]:
        return [
            self.app_resources_dir / "qml" / "main.qml",
            self.runtime_root / "qml" / "main.qml",
            self.runtime_root / "_internal" / "qml" / "main.qml",
            self.app_resources_dir / "Resources" / "qml" / "main.qml",
            self.runtime_root / "Resources" / "qml" / "main.qml",
        ]

    def _detect_resources_root(self) -> Path:
        candidates: list[Path] = [
            self.runtime_root / "_internal" / "resources",
            self.app_resources_dir / "resources",
            self.runtime_root / "resources",
            self.app_resources_dir / "Resources" / "resources",
            self.runtime_root / "Resources" / "resources",
            self.app_resources_dir,
        ]
        return next((c for c in candidates if c.is_dir()), self.app_resources_dir)

    def _detect_soundtrack_root(self) -> Path:
        candidates = [
            self.runtime_root / "_internal" / "soundtrack_tool" / "assets" / "SBY Soundtracks",
            self.runtime_root / "soundtrack_tool" / "assets" / "SBY Soundtracks",
            self.app_resources_dir / "soundtrack_tool" / "assets" / "SBY Soundtracks",
            self.app_resources_dir / "assets" / "SBY Soundtracks",
            self.resources_root / "SBY Soundtracks",
            self.app_resources_dir / "SBY Soundtracks",
        ]
        return next((c for c in candidates if c.is_dir()), candidates[-1])

    def _detect_variant(self) -> str:
        asset_mode = os.environ.get("SBY_ASSET_MODE", "").strip().lower()
        if asset_mode == "remote":
            return "remote"
        try:
            from .config import AssetMode, load_app_config  # Local import avoids circular deps

            config = load_app_config()
            if config.asset_mode == AssetMode.REMOTE or config.use_remote:
                return "remote"
        except Exception:
            pass
        executable = Path(sys.executable).stem if getattr(sys, "frozen", False) else ""
        if "remote" in executable.lower():
            return "remote"
        return "standard"

    def _determine_bundle_identifier(self) -> str:
        if self._variant == "remote":
            return "com.synthworks.sbyosttool.remote"
        return "com.synthworks.sbyosttool"

    def _determine_app_display_name(self) -> str:
        if self._variant == "remote":
            return "SBY OST Tool Remote"
        return "SBY OST Tool"


__all__ = ["ResourceLocator"]
