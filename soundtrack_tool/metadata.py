from __future__ import annotations

from pathlib import Path

from mutagen.flac import FLAC


def read_duration_string(path: Path) -> str:
    audio = FLAC(str(path))
    duration = int(audio.info.length)
    minutes = duration // 60
    seconds = duration % 60
    return f"{minutes}:{seconds:02d}"


def read_track_number(path: Path) -> int | None:
    audio = FLAC(str(path))
    try:
        value = audio.get("tracknumber")
        if not value:
            return None
        return int(value[0])
    except (ValueError, TypeError, IndexError):
        return None


def update_title_and_album(path: Path, *, title: str, album: str) -> None:
    audio = FLAC(str(path))
    audio["title"] = title
    audio["album"] = album
    audio.save()


def update_common_tags(
    path: Path,
    *,
    title: str,
    album: str,
    track_number: int | str,
    artist: str,
    album_artist: str,
    genre: str,
) -> None:
    audio = FLAC(str(path))
    audio["title"] = title
    audio["album"] = album
    audio["tracknumber"] = [str(track_number)]
    audio["artist"] = artist
    audio["albumartist"] = album_artist
    audio["genre"] = genre
    audio.save()


__all__ = [
    "read_duration_string",
    "read_track_number",
    "update_common_tags",
    "update_title_and_album",
]
