from __future__ import annotations

from pathlib import Path

from .environment import get_app_resources_dir, get_runtime_root


class ResourceLocator:
    """Resolves runtime and packaged resource paths cross platform."""

    def __init__(self, runtime_root: Path | None = None, resources_dir: Path | None = None) -> None:
        self._runtime_root = runtime_root or get_runtime_root()
        self._app_resources_dir = resources_dir or get_app_resources_dir(self._runtime_root)
        self._resources_root = self._detect_resources_root()
        self._soundtrack_root = self._detect_soundtrack_root()

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

    def main_qml_path(self) -> Path:
        return self.app_resources_dir / "main.qml"

    def application_icon_path(self, name: str = "icon.ico") -> Path:
        candidates = [
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
            self.app_resources_dir / "main.qml",
            self.runtime_root / "main.qml",
            self.runtime_root / "_internal" / "main.qml",
            self.app_resources_dir / "Resources" / "main.qml",
            self.runtime_root / "Resources" / "main.qml",
        ]

    def _detect_resources_root(self) -> Path:
        candidates: list[Path] = [
            self.app_resources_dir / "resources",
            self.runtime_root / "_internal" / "resources",
            self.runtime_root / "resources",
            self.app_resources_dir / "Resources" / "resources",
            self.runtime_root / "Resources" / "resources",
            self.app_resources_dir,
        ]
        return next((c for c in candidates if c.is_dir()), self.app_resources_dir)

    def _detect_soundtrack_root(self) -> Path:
        candidates = [
            self.runtime_root / "soundtrack_tool" / "assets" / "SBY Soundtracks",
            self.app_resources_dir / "assets" / "SBY Soundtracks",
            self.resources_root / "SBY Soundtracks",
            self.app_resources_dir / "SBY Soundtracks",
        ]
        return next((c for c in candidates if c.is_dir()), candidates[-1])


__all__ = ["ResourceLocator"]
