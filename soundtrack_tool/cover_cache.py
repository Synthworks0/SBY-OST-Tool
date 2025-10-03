from __future__ import annotations
import hashlib
import threading
from pathlib import Path
from typing import Iterable
from .cloudflare import R2Client


class CoverCache:
    """Caches remote cover art on disk so subsequent runs reuse it instantly."""

    def __init__(self, runtime_root: Path) -> None:
        self._cache_dir = runtime_root / "cache" / "covers"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def get_cover_path(self, relative_path: str, r2_client: R2Client) -> Path:
        destination = self._destination_for(relative_path)
        if destination.exists():
            return destination
        with self._lock:
            if destination.exists():
                return destination
            destination.parent.mkdir(parents=True, exist_ok=True)
            r2_client.download_file(relative_path, destination)
            return destination

    def prefetch_all(self, manifest_map: dict[str, dict], r2_client: R2Client) -> None:
        covers = set()
        for manifest in manifest_map.values():
            cover = manifest.get("cover")
            if cover:
                covers.add(cover)
            for track in manifest.get("tracks", []):
                track_cover = Path(track.get("relative_path", "")).parent / "cover.jpg"
                cover_str = str(track_cover).replace("\\", "/")
                if cover_str.strip("/"):
                    covers.add(cover_str)
        for cover_path in covers:
            try:
                self.get_cover_path(cover_path, r2_client)
            except Exception:
                # Ignore download errors during warmup; they'll be retried on demand.
                continue

    def _destination_for(self, relative_path: str) -> Path:
        normalised = relative_path.replace("\\", "/").strip("/")
        digest = hashlib.sha1(normalised.encode("utf-8")).hexdigest()
        suffix = Path(normalised).suffix or ".jpg"
        subdir = digest[:2]
        return self._cache_dir / subdir / f"{digest}{suffix}"


__all__ = ["CoverCache"]
