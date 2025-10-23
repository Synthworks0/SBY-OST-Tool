from __future__ import annotations
import re
import shutil
from collections import defaultdict
from contextlib import suppress
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple
import unicodedata
from threading import Event

from .albums import ALBUMS
from .asset_manifest import ASSET_MANIFEST
from .cloudflare import R2Client
from .config import AppConfig
from .metadata import read_track_number, update_common_tags, update_title_and_album
from .resources import ResourceLocator


@dataclass
class AlbumIntegrityReport:
    missing_tracks: list[str] = field(default_factory=list)
    misplaced_tracks: list[str] = field(default_factory=list)
    zero_byte_files: list[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not (self.missing_tracks or self.misplaced_tracks or self.zero_byte_files)

    def summary(self, album_title: str) -> str:
        parts: list[str] = []
        if self.missing_tracks:
            parts.append(
                f"Missing {len(self.missing_tracks)} track(s): {', '.join(self.missing_tracks)}"
            )
        if self.zero_byte_files:
            parts.append(
                f"Corrupted {len(self.zero_byte_files)} file(s): {', '.join(self.zero_byte_files)}"
            )
        if self.misplaced_tracks:
            parts.append(
                f"Misplaced track(s): {', '.join(self.misplaced_tracks)}"
            )
        detail = " ".join(parts) if parts else "Unknown issue."
        return (
            f"Error: Download incomplete for {album_title}. {detail} "
            "Please retry the extraction."
        )


class SoundtrackExtractor:
    """Handles copying bundled soundtracks, downloading from R2, and applying metadata."""

    COLLECTION_FOLDER_NAME = "SBY Soundtracks"

    def __init__(self, locator: ResourceLocator, config: AppConfig, r2_client: R2Client | None = None, cancel_event: Event | None = None) -> None:
        self._locator = locator
        self._config = config
        self._r2 = r2_client
        self._use_remote = config.use_remote and r2_client is not None
        self._lazy_remote_error: str | None = None
        self._cancel_event = cancel_event

    def ensure_collection_root(self, output_folder: Path) -> Path:
        target = output_folder / self.COLLECTION_FOLDER_NAME
        target.mkdir(parents=True, exist_ok=True)
        return target

    def album_states(self, output_folder: Path) -> dict[str, str]:
        base = self.ensure_collection_root(output_folder)
        states: dict[str, str] = {}
        for album_name in ALBUMS:
            existing = self.find_existing_album_dir(output_folder, album_name, base)
            states[album_name] = "rename" if existing else "extract"
        return states

    def find_existing_album_dir(
        self,
        output_folder: Path,
        album_name: str,
        collection_root: Path | None = None,
    ) -> Path | None:
        album_data = ALBUMS.get(album_name)
        if not album_data:
            return None
        root = collection_root or self.ensure_collection_root(output_folder)
        candidate_names: list[str] = []
        for key in ("Japanese", "Romaji", "English"):
            name = album_data.get(key)
            if name:
                candidate_names.append(name)
        seen: set[str] = set()
        for name in candidate_names:
            if name in seen:
                continue
            seen.add(name)
            candidate = root / name
            if candidate.exists() and any(candidate.iterdir()):
                return candidate
        return None

    def extract_album(
        self,
        album_name: str,
        language: str,
        include_track_numbers: bool,
        output_folder: Path,
    ) -> Tuple[bool, str]:
        if self._use_remote:
            return self._download_remote_album(album_name, output_folder)

        album_data = ALBUMS.get(album_name)
        if not album_data:
            return False, f"Error: Unknown album '{album_name}'"
        source_dir = self._locator.soundtrack_source_dir(album_data["English"])
        if not source_dir.exists():
            if self._ensure_remote_client():
                return self._download_remote_album(album_name, output_folder)
            return False, f"Error: Soundtrack files not found at {source_dir}"

        collection_root = self.ensure_collection_root(output_folder)
        destination = collection_root / album_data.get(language, album_data["English"])
        destination.mkdir(parents=True, exist_ok=True)

        if (source_dir / "cover.jpg").exists():
            shutil.copy2(source_dir / "cover.jpg", destination / "cover.jpg")

        if album_name == "Extras":
            self._extract_extras(source_dir, destination, language)
        else:
            self._extract_regular_album(source_dir, destination, include_track_numbers)

        localized_name = album_data.get(language, album_name)
        return True, f"Soundtrack '{localized_name}' extracted successfully"

    def rename_album(
        self,
        album_name: str,
        language: str,
        include_track_numbers: bool,
        output_folder: Path,
    ) -> Tuple[bool, str]:
        album_data = ALBUMS.get(album_name)
        if not album_data:
            return False, f"Error: Unknown album '{album_name}'"
        root = self.ensure_collection_root(output_folder)
        target_dir = root / album_data.get(language, album_data["English"])
        english_dir = root / album_data.get("English", album_data.get(language, ""))

        if target_dir != english_dir and english_dir.exists():
            if not target_dir.exists():
                english_dir.rename(target_dir)
            else:
                for item in english_dir.iterdir():
                    destination = target_dir / item.name
                    if destination.exists():
                        if destination.is_dir():
                            shutil.rmtree(destination)
                        else:
                            destination.unlink()
                    shutil.move(str(item), str(destination))
                shutil.rmtree(english_dir)

        if not target_dir.exists():
            for lang in ("English", "Romaji", "Japanese"):
                fallback_name = album_data.get(lang)
                if fallback_name:
                    candidate = root / fallback_name
                    if candidate.exists():
                        candidate.rename(target_dir)
                        break
        if not target_dir.exists():
            return False, f"Error: No files found for {album_data.get(language, album_data['English'])}"

        if album_name == "Extras":
            return self._rename_extras(target_dir, language)
        return self._rename_regular(album_name, target_dir, language, include_track_numbers)

    def destination_album_dir(self, output_folder: Path, album_name: str, language: str) -> Path:
        root = output_folder / self.COLLECTION_FOLDER_NAME
        return root / ALBUMS[album_name].get(language, ALBUMS[album_name]["English"])

    def expected_track_count(self, album_name: str, language: str) -> int:
        album = ALBUMS.get(album_name)
        if not album:
            return 0
        if album_name == "Extras":
            return len(ALBUMS["Extras"]["Tracks"])
        tracks = album.get("Tracks", {})
        return len(tracks.get(language, []))

    def locate_album_dir(
        self,
        output_folder: Path,
        album_name: str,
        language: str,
    ) -> Tuple[Path | None, str]:
        album_data = ALBUMS.get(album_name)
        if not album_data:
            return None, language
        collection_root = self.ensure_collection_root(output_folder)
        preferred_name = album_data.get(language, album_data.get("English", album_name))
        target_dir = collection_root / preferred_name
        effective_language = language
        if not target_dir.exists():
            fallback_dir = self.find_existing_album_dir(output_folder, album_name, collection_root)
            if fallback_dir:
                fallback_name = fallback_dir.name
                fallback_language = self._language_for_directory(album_data, fallback_name)
                if fallback_language:
                    effective_language = fallback_language
                target_dir = fallback_dir
            else:
                return None, language
        return target_dir, effective_language

    def count_effective_tracks(self, output_folder: Path, album_name: str, language: str) -> int:
        target_dir, _ = self.locate_album_dir(output_folder, album_name, language)
        if not target_dir:
            return 0
        if not target_dir.exists():
            return 0
        if album_name == "Extras":
            return sum(1 for p in target_dir.rglob("*.flac") if p.is_file() and p.stat().st_size > 0)
        return sum(1 for p in target_dir.glob("*.flac") if p.is_file() and p.stat().st_size > 0)

    def count_available_tracks(self, output_folder: Path, album_name: str, language: str) -> int:
        return self.count_effective_tracks(output_folder, album_name, language)

    # --- Local extraction helpers -----------------------------------------------------

    def _extract_regular_album(self, source_dir: Path, destination: Path, include_numbers: bool) -> None:
        flac_files = sorted(source_dir.glob("*.flac"))
        for index, path in enumerate(flac_files, start=1):
            self._check_cancel()
            base_name = re.sub(r"^\d+\.\s*", "", path.stem)
            if include_numbers:
                filename = f"{index:02d}. {base_name}.flac"
            else:
                filename = f"{base_name}.flac"
            shutil.copy2(path, destination / filename)

    def _extract_extras(self, source_dir: Path, destination: Path, language: str) -> None:
        for track in ALBUMS["Extras"]["Tracks"]:
            self._check_cancel()
            subfolder_info = track.get("subfolder", {})
            filename = track.get("filename")
            source_folder = source_dir
            if subfolder_info:
                english_name = subfolder_info.get("English")
                if english_name:
                    source_folder = source_folder.joinpath(*english_name.split("/"))
            if not source_folder.exists():
                continue
            dest_folder = destination
            if subfolder_info:
                target_name = subfolder_info.get(language)
                if target_name:
                    dest_folder = destination.joinpath(*target_name.split("/"))
            dest_folder.mkdir(parents=True, exist_ok=True)

            if filename:
                candidate = source_folder / filename
                if candidate.exists():
                    shutil.copy2(candidate, dest_folder / candidate.name)
            cover_source = source_folder / "cover.jpg"
            if cover_source.exists():
                shutil.copy2(cover_source, dest_folder / "cover.jpg")

    # --- Remote extraction helpers ----------------------------------------------------

    def _ensure_remote_client(self) -> bool:
        """Ensure a remote client is available before performing remote operations."""
        if self._use_remote:
            return True
        if not self._config.use_remote:
            return False
        if self._r2 is None:
            try:
                self._r2 = R2Client(self._config, cancel_event=self._cancel_event)
            except Exception as exc:
                self._lazy_remote_error = str(exc)
                return False
        self._lazy_remote_error = None
        self._use_remote = True
        return True

    def _download_remote_album(self, album_name: str, output_folder: Path) -> Tuple[bool, str]:
        if not self._ensure_remote_client():
            detail = self._lazy_remote_error or "Cloudflare R2 client not configured"
            return False, f"Error: Remote download unavailable ({detail})"
        manifest = ASSET_MANIFEST.get(album_name)
        if not manifest:
            return False, f"Error: Remote manifest missing for '{album_name}'"

        album_data = ALBUMS.get(album_name)
        if not album_data:
            return False, f"Error: Unknown album '{album_name}'"

        collection_root = self.ensure_collection_root(output_folder)
        base_dir = collection_root / album_data["English"]
        base_dir.mkdir(parents=True, exist_ok=True)

        cover_rel = manifest.get("cover")
        if cover_rel:
            self._download_path(cover_rel, base_dir / "cover.jpg", optional=True)

        if album_name == "Extras":
            self._download_remote_extras(manifest, base_dir)
        else:
            self._download_remote_regular(manifest, base_dir)

        return True, f"Soundtrack '{album_name}' downloaded successfully"

    def _download_remote_regular(self, manifest: dict, base_dir: Path) -> None:
        downloaded_covers: set[Path] = set()
        for track in manifest.get("tracks", []):
            self._check_cancel()
            relative = track["relative_path"]
            sub_path = Path(relative)
            if sub_path.parts:
                sub_path = Path(*sub_path.parts[1:])  # strip album folder name
            destination = base_dir / sub_path
            self._download_path(relative, destination)
            cover_remote = Path(relative).with_name("cover.jpg")
            cover_local = destination.parent / "cover.jpg"
            if cover_local not in downloaded_covers:
                self._download_path(cover_remote.as_posix(), cover_local, optional=True)
                downloaded_covers.add(cover_local)

    def _download_remote_extras(self, manifest: dict, base_dir: Path) -> None:
        downloaded_covers: set[Path] = set()
        for track in manifest.get("tracks", []):
            self._check_cancel()
            relative = track["relative_path"]
            sub_path = Path(relative)
            if sub_path.parts:
                sub_path = Path(*sub_path.parts[1:])  # strip top-level Extras directory
            destination = base_dir / sub_path
            self._download_path(relative, destination)
            cover_remote = Path(relative).parent / "cover.jpg"
            cover_local = destination.parent / "cover.jpg"
            if cover_local not in downloaded_covers:
                self._download_path(cover_remote.as_posix(), cover_local, optional=True)
                downloaded_covers.add(cover_local)

    def _download_path(self, relative_path: str, destination: Path, *, optional: bool = False) -> None:
        if not self._r2:
            if optional:
                return
            raise RuntimeError("Cloudflare R2 client not configured")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            try:
                if destination.stat().st_size > 0:
                    return
            except OSError:
                pass
            with suppress(OSError):
                destination.unlink(missing_ok=True)
        try:
            self._r2.download_file(relative_path, destination)
        except Exception:
            if optional:
                return
            raise

    # --- Integrity helpers -------------------------------------------------------------

    @staticmethod
    def _normalize_title_key(value: str | None) -> str:
        if not value:
            return ""
        normalised = unicodedata.normalize("NFKC", value)
        cleaned = re.sub(r"[\s\u3000\-_.()'\"!?、。・＆&:;【】「」『』\[\]]+", "", normalised)
        return cleaned.lower()

    @staticmethod
    def _format_regular_track_label(index: int, title: str) -> str:
        return f"{index:02d} - {title}"

    @staticmethod
    def _guess_track_number(path: Path) -> int | None:
        match = re.match(r"^\s*(\d{1,2})", path.stem)
        if match:
            value = int(match.group(1))
            if value > 0:
                return value
        return None

    @staticmethod
    def _extras_track_label(track: dict, language: str) -> str:
        titles = track.get("titles", {})
        for key in (language, "English", "Romaji", "Japanese"):
            value = titles.get(key)
            if value:
                return value
        filename = track.get("filename")
        if filename:
            return Path(filename).stem
        return "Unknown track"

    def _expected_extras_folder(self, extras_dir: Path, track: dict, language: str) -> Path:
        subfolder = track.get("subfolder", {})
        if not subfolder:
            return extras_dir
        for key in (language, "English", "Romaji", "Japanese"):
            folder = subfolder.get(key)
            if folder:
                return extras_dir.joinpath(*folder.split("/"))
        return extras_dir

    @staticmethod
    def _language_for_directory(album_data: dict, dirname: str) -> str:
        for key in ("Japanese", "Romaji", "English"):
            if album_data.get(key) == dirname:
                return key
        return ""

    def verify_album_integrity(
        self,
        album_name: str,
        language: str,
        include_track_numbers: bool,
        output_folder: Path,
    ) -> AlbumIntegrityReport:
        report = AlbumIntegrityReport()
        album_data = ALBUMS.get(album_name)
        if not album_data:
            return report

        collection_root = self.ensure_collection_root(output_folder)
        preferred_name = album_data.get(language, album_data.get("English", album_name))
        target_dir = collection_root / preferred_name
        effective_language = language

        if not target_dir.exists():
            fallback_dir = self.find_existing_album_dir(output_folder, album_name, collection_root)
            if fallback_dir:
                fallback_name = fallback_dir.name
                fallback_language = self._language_for_directory(album_data, fallback_name)
                if fallback_language:
                    effective_language = fallback_language
                target_dir = fallback_dir
            else:
                report.missing_tracks.append(f"{preferred_name} (folder missing)")
                return report

        if album_name == "Extras":
            self._verify_extras_album(target_dir, effective_language, report)
        else:
            self._verify_regular_album(
                album_name,
                target_dir,
                effective_language,
                include_track_numbers,
                report,
            )

        return report

    def _verify_regular_album(
        self,
        album_name: str,
        album_dir: Path,
        language: str,
        include_numbers: bool,
        report: AlbumIntegrityReport,
    ) -> None:
        track_titles = ALBUMS[album_name]["Tracks"].get(language, [])
        if not track_titles:
            return
        _ = include_numbers

        title_map: dict[str, list[Path]] = defaultdict(list)
        number_map: dict[int, list[Path]] = defaultdict(list)
        zero_byte_paths: set[Path] = set()

        for candidate in sorted(album_dir.glob("*.flac")):
            title_key = self._normalize_title_key(re.sub(r"^\d+\.\s*", "", candidate.stem))
            if title_key:
                title_map[title_key].append(candidate)
            track_number = read_track_number(candidate)
            if track_number is None:
                track_number = self._guess_track_number(candidate)
            if track_number is not None:
                number_map[track_number].append(candidate)
            try:
                if candidate.stat().st_size == 0:
                    zero_byte_paths.add(candidate)
            except OSError:
                zero_byte_paths.add(candidate)

        def take_from_map(container: dict, key):
            bucket = container.get(key)
            if not bucket:
                return None
            result = bucket.pop(0)
            if not bucket:
                container.pop(key, None)
            return result

        def remove_from_number_map(path: Path) -> None:
            for idx in list(number_map.keys()):
                bucket = number_map[idx]
                with suppress(ValueError):
                    bucket.remove(path)
                if not bucket:
                    number_map.pop(idx, None)

        for index, title in enumerate(track_titles, start=1):
            label = self._format_regular_track_label(index, title)
            key = self._normalize_title_key(title)
            matched = take_from_map(title_map, key)

            if matched is None:
                matched = take_from_map(number_map, index)

            if matched is None:
                report.missing_tracks.append(label)
                continue

            remove_from_number_map(matched)

            if matched in zero_byte_paths:
                report.zero_byte_files.append(label)

    def _verify_extras_album(
        self,
        extras_dir: Path,
        language: str,
        report: AlbumIntegrityReport,
    ) -> None:
        track_list = ALBUMS.get("Extras", {}).get("Tracks", [])
        if not track_list:
            return

        title_map: dict[str, list[Path]] = defaultdict(list)
        zero_byte_paths: set[Path] = set()

        for candidate in sorted(extras_dir.rglob("*.flac")):
            key = self._normalize_title_key(candidate.stem)
            if key:
                title_map[key].append(candidate)
            try:
                if candidate.stat().st_size == 0:
                    zero_byte_paths.add(candidate)
            except OSError:
                zero_byte_paths.add(candidate)

        def take_from_title_map(key: str):
            bucket = title_map.get(key)
            if not bucket:
                return None
            result = bucket.pop(0)
            if not bucket:
                title_map.pop(key, None)
            return result

        for track in track_list:
            label = self._extras_track_label(track, language)
            titles = track.get("titles", {}) or {}
            search_terms: list[str] = []
            for key in (language, "English", "Romaji", "Japanese"):
                term = titles.get(key)
                if term:
                    search_terms.append(term)
            filename = track.get("filename")
            if filename:
                search_terms.append(Path(filename).stem)
            normalized_terms = [
                self._normalize_title_key(term) for term in search_terms if term
            ]

            matched: Path | None = None
            for term in normalized_terms:
                matched = take_from_title_map(term)
                if matched:
                    break

            if matched is None:
                report.missing_tracks.append(label)
                continue

            if matched in zero_byte_paths:
                report.zero_byte_files.append(label)

            expected_folder = self._expected_extras_folder(extras_dir, track, language)
            if expected_folder.exists():
                if expected_folder not in matched.parents:
                    current_rel = matched.parent.relative_to(extras_dir)
                    expected_rel = expected_folder.relative_to(extras_dir)
                    report.misplaced_tracks.append(
                        f"{label} (found in '{current_rel.as_posix()}', expected '{expected_rel.as_posix()}')"
                    )
            elif expected_folder != extras_dir:
                expected_rel = expected_folder.relative_to(extras_dir)
                report.misplaced_tracks.append(
                    f"{label} (expected folder '{expected_rel.as_posix()}' missing)"
                )

    # --- Rename helpers ---------------------------------------------------------------

    def _rename_regular(
        self,
        album_name: str,
        album_dir: Path,
        language: str,
        include_numbers: bool,
    ) -> Tuple[bool, str]:
        track_names = ALBUMS[album_name]["Tracks"].get(language, [])
        if not track_names:
            return False, f"Error: Missing track listing for {language}"
        files_renamed = 0
        for idx, path in enumerate(sorted(album_dir.glob("*.flac"), key=lambda p: p.stat().st_mtime), start=1):
            self._check_cancel()
            track_number = read_track_number(path)
            if track_number is None or track_number < 1 or track_number > len(track_names):
                stem = path.stem.lstrip()
                guess = None
                if len(stem) >= 2 and stem[:2].isdigit():
                    guess = int(stem[:2])
                elif stem and stem[0].isdigit():
                    token = stem.split(" ", 1)[0]
                    if token.isdigit():
                        guess = int(token)
                if guess is None or guess < 1 or guess > len(track_names):
                    guess = idx if idx <= len(track_names) else None
                track_number = guess
            if track_number is None:
                continue
            title = track_names[track_number - 1]
            if include_numbers:
                new_name = f"{track_number:02d}. {title}.flac"
            else:
                new_name = f"{title}.flac"
            new_path = album_dir / new_name
            if new_path != path:
                if new_path.exists():
                    new_path.unlink()
                path.rename(new_path)
                path = new_path
            update_title_and_album(path, title=title, album=ALBUMS[album_name][language])
            files_renamed += 1
        if files_renamed == 0:
            return False, f"Error: No matching files found for {ALBUMS[album_name][language]}"
        return True, f"Files renamed successfully for {ALBUMS[album_name][language]}"

    def _rename_extras(self, extras_dir: Path, language: str) -> Tuple[bool, str]:
        track_list = ALBUMS["Extras"]["Tracks"]
        files_renamed = 0
        processed_paths: set[Path] = set()

        album_parent_dir = extras_dir.parent
        desired_dir = album_parent_dir / ALBUMS["Extras"].get(language, ALBUMS["Extras"]["English"])
        if extras_dir != desired_dir:
            if desired_dir.exists():
                shutil.rmtree(desired_dir)
            extras_dir.rename(desired_dir)
            extras_dir = desired_dir

        for old_path, new_path in self._planned_subfolder_moves(extras_dir, track_list, language):
            self._check_cancel()
            if old_path == new_path:
                continue
            if not old_path.exists():
                continue
            new_path.parent.mkdir(parents=True, exist_ok=True)
            if new_path.exists():
                for item in old_path.iterdir():
                    destination = new_path / item.name
                    if destination.exists():
                        if item.is_dir():
                            shutil.rmtree(destination)
                        else:
                            destination.unlink()
                    shutil.move(str(item), str(destination))
                old_path.rmdir()
            else:
                old_path.rename(new_path)

        for track in track_list:
            self._check_cancel()
            subfolder = track.get("subfolder", {})
            target_folder = extras_dir
            if subfolder:
                name = subfolder.get(language)
                if name:
                    target_folder = extras_dir.joinpath(*name.split("/"))
            if not target_folder.exists():
                continue
            source_file = self._locate_extras_track(target_folder, track)
            if not source_file or not source_file.exists():
                for candidate in sorted(target_folder.glob("*.flac")):
                    if candidate not in processed_paths:
                        source_file = candidate
                        break
            if not source_file or not source_file.exists():
                continue

            title = track.get("titles", {}).get(language, source_file.stem)
            album_title = track.get("album_title", {}).get(language, "")
            track_number = track.get("track_number", 1)
            contributing_artist = track.get("contributing_artists", {}).get(language, "")
            album_artist = track.get("album_artists", {}).get(language, "")
            genre = track.get("genre", "")

            new_name = track.get("filename") or source_file.name
            if title:
                new_name = f"{title}{source_file.suffix}"
            destination = target_folder / new_name
            if destination != source_file:
                if destination.exists():
                    destination.unlink()
                source_file.rename(destination)
            update_common_tags(
                destination,
                title=title,
                album=album_title,
                track_number=track_number,
                artist=contributing_artist,
                album_artist=album_artist,
                genre=genre,
            )
            processed_paths.add(destination)
            files_renamed += 1

        if files_renamed == 0:
            extras_title = ALBUMS["Extras"].get(language, ALBUMS["Extras"]["English"])
            return False, f"Error: No matching files found for {extras_title}"
        extras_title = ALBUMS["Extras"].get(language, ALBUMS["Extras"]["English"])
        return True, f"Files renamed successfully for {extras_title}"

    # --- Cancellation helpers ---------------------------------------------------------

    def _check_cancel(self) -> None:
        if self._cancel_event is not None and self._cancel_event.is_set():
            raise RuntimeError("Operation cancelled")

    def _planned_subfolder_moves(self, extras_dir: Path, track_list: list[dict], language: str):
        renames: list[tuple[Path, Path]] = []
        for track in track_list:
            subfolder = track.get("subfolder", {})
            target = subfolder.get(language)
            if not target:
                continue
            current = self._find_existing_subfolder(extras_dir, subfolder)
            if not current:
                continue
            desired = extras_dir.joinpath(*target.split("/"))
            if current != desired:
                renames.append((current, desired))
        renames.sort(key=lambda pair: pair[0].as_posix().count("/"), reverse=True)
        return renames

    def _find_existing_subfolder(self, root: Path, subfolder: dict) -> Path | None:
        for lang in ("Japanese", "Romaji", "English"):
            name = subfolder.get(lang)
            if not name:
                continue
            candidate = root.joinpath(*name.split("/"))
            if candidate.exists():
                return candidate
        return None

    def _locate_extras_track(self, folder: Path, track: dict) -> Path | None:
        filename = track.get("filename")
        if filename:
            candidate = folder / filename
            if candidate.exists():
                return candidate
        track_number = track.get("track_number")
        for candidate in folder.glob("*.flac"):
            existing_number = read_track_number(candidate)
            if existing_number is not None and track_number is not None and existing_number == track_number:
                return candidate
        return None


__all__ = ["SoundtrackExtractor", "AlbumIntegrityReport"]
