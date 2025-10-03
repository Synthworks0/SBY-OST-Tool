from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .albums import ALBUMS
from .asset_manifest import ASSET_MANIFEST
from .config import AppConfig
from .metadata import read_duration_string, read_track_number
from .resources import ResourceLocator


@dataclass(frozen=True)
class SongEntry:
    title: str
    length: str
    source: str
    track_number: int
    is_remote: bool
    relative_path: Optional[str] = None

class AudioCatalog:
    def __init__(self, locator: ResourceLocator, config: AppConfig, r2_client=None) -> None:
        self._locator = locator
        self._config = config
        self._r2 = r2_client
        self._use_remote = config.use_remote and r2_client is not None

    def build(self, album_name: str, language: str) -> list[SongEntry]:
        if self._use_remote:
            return self._build_remote(album_name, language)

        album_data = ALBUMS.get(album_name)
        if not album_data:
            return []
        source_dir = self._locator.soundtrack_source_dir(album_data["English"])
        if not source_dir.exists():
            return []
        if album_name == "Extras":
            return self._build_local_extras(source_dir, language)
        return self._build_local_standard(source_dir, album_data["Tracks"].get(language, []))

    def _build_local_standard(self, source_dir: Path, track_titles: list[str]) -> list[SongEntry]:
        entries: list[SongEntry] = []
        flac_files = sorted(source_dir.glob("*.flac"))
        for idx, song_path in enumerate(flac_files, start=1):
            title = track_titles[idx - 1] if idx - 1 < len(track_titles) else song_path.stem
            length = read_duration_string(song_path)
            track_number = read_track_number(song_path) or idx
            entries.append(
                SongEntry(
                    title=title,
                    length=length,
                    source=str(song_path),
                    track_number=track_number,
                    is_remote=False,
                    relative_path=str(song_path.relative_to(self._locator.soundtrack_collection_root())).replace('\\', '/'),
                )
            )
        return entries

    def _build_local_extras(self, album_dir: Path, language: str) -> list[SongEntry]:
        entries: list[SongEntry] = []
        for track in ALBUMS["Extras"]["Tracks"]:
            song_path = self._resolve_extras_track_path(album_dir, track)
            if not song_path or not song_path.exists():
                continue
            titles = track.get("titles", {})
            title = titles.get(language) or song_path.stem
            length = read_duration_string(song_path)
            track_number = read_track_number(song_path) or track.get("track_number", 0)
            entries.append(
                SongEntry(
                    title=title,
                    length=length,
                    source=str(song_path),
                    track_number=track_number,
                    is_remote=False,
                    relative_path=str(song_path.relative_to(self._locator.soundtrack_collection_root())).replace('\\', '/'),
                )
            )
        return entries

    def _build_remote(self, album_name: str, language: str) -> list[SongEntry]:
        if not self._r2:
            return []
        manifest = ASSET_MANIFEST.get(album_name)
        if not manifest:
            return []

        entries: list[SongEntry] = []
        tracks_manifest = manifest.get("tracks", [])

        if album_name == "Extras":
            for track in ALBUMS["Extras"]["Tracks"]:
                manifest_entry = self._match_remote_extras_track(manifest, track)
                if not manifest_entry:
                    continue
                relative_path = manifest_entry["relative_path"]
                title = track.get("titles", {}).get(language) or Path(relative_path).stem
                length = _format_duration(manifest_entry.get("duration_seconds"))
                url = self._r2.build_url(relative_path)
                entries.append(
                    SongEntry(
                        title=title,
                        length=length,
                        source=url,
                        track_number=track.get("track_number", 0) or 0,
                        is_remote=True,
                        relative_path=relative_path,
                    )
                )
        else:
            manifest_by_number = {item.get("track_number"): item for item in tracks_manifest}
            track_titles = ALBUMS[album_name]["Tracks"].get(language, [])
            for idx, title in enumerate(track_titles, start=1):
                manifest_entry = manifest_by_number.get(idx)
                if not manifest_entry:
                    continue
                relative_path = manifest_entry["relative_path"]
                length = _format_duration(manifest_entry.get("duration_seconds"))
                url = self._r2.build_url(relative_path)
                entries.append(
                    SongEntry(
                        title=title,
                        length=length,
                        source=url,
                        track_number=idx,
                        is_remote=True,
                        relative_path=relative_path,
                    )
                )
        return entries

    @staticmethod
    def _normalise_relative_path(relative_path: str | None) -> str:
        if not relative_path:
            return ""
        return relative_path.replace("\\", "/").lstrip("./")

    def _match_remote_extras_track(self, manifest: dict, track: dict) -> dict | None:
        candidates = manifest.get("tracks", [])
        relative = track.get("relative_path")
        if relative:
            rel_norm = self._normalise_relative_path(relative)
            for item in candidates:
                if self._normalise_relative_path(item.get("relative_path")) == rel_norm:
                    return item

        filename = (track.get("filename") or "").lower()
        subfolder = track.get("subfolder", {}).get("English", "")
        subfolder_norm = self._normalise_relative_path(subfolder).lower()
        if filename:
            for item in candidates:
                rel_norm = self._normalise_relative_path(item.get("relative_path"))
                rel_lower = rel_norm.lower()
                if rel_lower.endswith(filename):
                    if subfolder_norm:
                        if subfolder_norm in rel_lower:
                            return item
                    else:
                        return item

        number = track.get("track_number")
        if number is not None:
            for item in candidates:
                if item.get("track_number") == number:
                    return item
        return None

    def _resolve_extras_track_path(self, album_dir: Path, track: dict) -> Path | None:
        filename = track.get("filename")
        subfolder = track.get("subfolder")
        base_dir = album_dir
        if subfolder:
            english_name = subfolder.get("English")
            if english_name:
                base_dir = album_dir.joinpath(*english_name.split("/"))
        if not base_dir.exists():
            return None
        if filename:
            candidate = base_dir / filename
            if candidate.exists():
                return candidate
        flacs = sorted(base_dir.glob("*.flac"))
        return flacs[0] if flacs else None

def _format_duration(duration: Optional[int]) -> str:
    if not duration:
        return "??:??"
    minutes, seconds = divmod(int(duration), 60)
    return f"{minutes}:{seconds:02d}"


__all__ = ["AudioCatalog", "SongEntry"]
