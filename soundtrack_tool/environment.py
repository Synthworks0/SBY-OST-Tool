from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_MEDIA_BACKEND = "ffmpeg"


def get_runtime_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def get_app_resources_dir(runtime_root: Path | None = None) -> Path:
    runtime = runtime_root or get_runtime_root()
    if getattr(sys, "frozen", False) and sys.platform == "darwin":
        candidate = (runtime / ".." / "Resources").resolve()
        if candidate.is_dir():
            return candidate
    return runtime


def _merge_env_paths(env_key: str, candidates: Sequence[Path], logger=None) -> None:
    existing = os.environ.get(env_key, "")
    merged: list[str] = []
    for path in candidates:
        if path.is_dir():
            merged.append(str(path))
    if existing:
        merged.extend(p for p in existing.split(os.pathsep) if p)
    if merged:
        os.environ[env_key] = os.pathsep.join(dict.fromkeys(merged))
        if logger:
            logger.info(f"Set {env_key}={os.environ[env_key]}")


def _set_platform_plugin_path(plugin_roots: Sequence[Path], logger=None) -> None:
    for root in plugin_roots:
        platforms = root / "platforms"
        if platforms.is_dir():
            os.environ.setdefault("QT_QPA_PLATFORM_PLUGIN_PATH", str(platforms))
            if logger:
                logger.info(f"QT_QPA_PLATFORM_PLUGIN_PATH={platforms}")
            break


def configure_qt_environment(logger=None) -> None:
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ.setdefault("QT_MEDIA_BACKEND", DEFAULT_MEDIA_BACKEND)
    os.environ.setdefault("QT_MULTIMEDIA_PREFERRED_PLUGINS", DEFAULT_MEDIA_BACKEND)

    runtime_root = get_runtime_root()
    resources_dir = get_app_resources_dir(runtime_root)

    if sys.platform == "darwin":
        os.environ.setdefault("QT_QPA_PLATFORM", "cocoa")
    elif sys.platform.startswith("linux"):
        os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

    plugin_candidates: tuple[Path, ...] = (
        runtime_root / "PySide6" / "Qt" / "plugins",
        resources_dir / "PySide6" / "Qt" / "plugins",
        runtime_root / "Qt" / "plugins",
        resources_dir / "Qt" / "plugins",
        runtime_root / "_internal" / "PySide6" / "plugins",
    )
    qml_candidates: tuple[Path, ...] = (
        runtime_root / "PySide6" / "Qt" / "qml",
        resources_dir / "PySide6" / "Qt" / "qml",
        runtime_root / "_internal" / "PySide6" / "qml",
    )

    _merge_env_paths("QT_PLUGIN_PATH", plugin_candidates, logger)
    _merge_env_paths("QML2_IMPORT_PATH", qml_candidates, logger)
    _set_platform_plugin_path(plugin_candidates, logger)


__all__ = [
    "configure_qt_environment",
    "get_app_resources_dir",
    "get_runtime_root",
]
