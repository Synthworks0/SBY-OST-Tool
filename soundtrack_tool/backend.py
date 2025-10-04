from __future__ import annotations
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PySide6.QtCore import QObject, Property, QTimer, QUrl, Signal, Slot, QCoreApplication
from PySide6.QtCore import QDir
from threading import Event

from .albums import ALBUMS
from .asset_manifest import ASSET_MANIFEST
from .audio_catalog import AudioCatalog
from .cloudflare import R2Client
from .config import AppConfig, load_app_config
from .extractor import AlbumIntegrityReport, SoundtrackExtractor
from .filesystem import FileSystemService
from .resources import ResourceLocator
from .settings import AppSettings
from .cover_cache import CoverCache


class RenamerBackend(QObject):
    albumsChanged = Signal()
    coverImageChanged = Signal()
    outputFolderChanged = Signal()
    folderContentsChanged = Signal()
    driveListChanged = Signal()
    extractionFinished = Signal(str)
    extractionStateChanged = Signal(bool)
    albumStateChanged = Signal()
    currentAlbumChanged = Signal()
    currentLanguageChanged = Signal()
    canExtractChanged = Signal()
    songListChanged = Signal()
    currentPathChanged = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.albums = ALBUMS
        self._locator = ResourceLocator()
        self._filesystem = FileSystemService()
        self._config: AppConfig = load_app_config()
        self._cancel_event: Event = Event()
        self._r2_client = R2Client(self._config, cancel_event=self._cancel_event) if self._config.use_remote else None
        self._extractor = SoundtrackExtractor(self._locator, self._config, self._r2_client, cancel_event=self._cancel_event)
        self._audio_catalog = AudioCatalog(self._locator, self._config, self._r2_client)
        self._settings = AppSettings(self._locator.runtime_root / "config.json")
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._pending_futures: list = []
        self._cover_cache = CoverCache(self._locator.runtime_root) if self._config.use_remote else None
        if self._config.use_remote and self._r2_client and self._cover_cache:
            self._track_future(self._executor.submit(self._cover_cache.prefetch_all, ASSET_MANIFEST, self._r2_client))

        QDir.addSearchPath("resources", str(self._locator.resources_root))

        self._current_album = next(iter(self.albums))
        self._current_language = "English"
        self._output_folder = ""
        self._current_path = ""
        self._folder_contents: list[dict[str, object]] = []
        self._drive_list: list[str] = []
        self._album_states: dict[str, str] = {name: "extract" for name in self.albums}
        self._song_list: list[dict[str, str]] = []
        self._include_track_numbers = True
        self._is_extracting = False

        self._load_last_output_folder()
        self.update_song_list()
        QTimer.singleShot(0, self.initialize_file_system)

        app = QCoreApplication.instance()
        if app is not None:
            try:
                app.aboutToQuit.connect(self._shutdown)  # type: ignore[attr-defined]
            except Exception:
                pass

    def initialize_file_system(self) -> None:
        self._drive_list = self._filesystem.list_drives()
        self.driveListChanged.emit()
        self.update_folder_contents()

    @Property(str, notify=outputFolderChanged)
    def output_folder(self) -> str:
        return self._output_folder

    @Property(str, notify=currentAlbumChanged)
    def current_album(self) -> str:
        return self._current_album

    def _load_last_output_folder(self) -> None:
        last_folder = self._settings.load_last_output_folder()
        if last_folder:
            self._output_folder = last_folder
            self.outputFolderChanged.emit()
            self.check_and_create_soundtracks()
            self.update_song_list()

    def _persist_output_folder(self) -> None:
        self._settings.save_last_output_folder(self._output_folder)

    @Slot(str)
    def set_output_folder(self, folder: str) -> None:
        if self._output_folder == folder:
            return
        self._output_folder = folder
        self.outputFolderChanged.emit()
        self._persist_output_folder()
        self.check_and_create_soundtracks()
        self.canExtractChanged.emit()

    @Property('QVariantList', notify=driveListChanged)
    def drive_list(self) -> list[str]:
        return self._drive_list

    @Property('QVariantList', notify=folderContentsChanged)
    def folder_contents(self) -> list[dict[str, object]]:
        return self._folder_contents

    @Property(bool, constant=True)
    def is_frozen(self) -> bool:
        return getattr(sys, 'frozen', False)

    @Property(bool, constant=True)
    def is_remote_enabled(self) -> bool:
        return self._config.use_remote

    @Property(bool, notify=extractionStateChanged)
    def is_extracting(self) -> bool:
        return self._is_extracting

    @Slot(str)
    def set_current_path(self, path: str) -> None:
        if self._current_path == path:
            return
        self._current_path = path
        self.currentPathChanged.emit()
        self.update_folder_contents()

    @Slot()
    def update_folder_contents(self) -> None:
        if not self._current_path:
            self._folder_contents = [{"name": drive, "path": drive, "isDir": True} for drive in self._drive_list]
        else:
            self._folder_contents = self._filesystem.list_directory(self._current_path)
        self.folderContentsChanged.emit()

    @Slot(str, result=str)
    def get_parent_directory(self, path: str) -> str:
        return self._filesystem.parent(path)

    @Slot(str, str, result=bool)
    def create_new_folder(self, parent_path: str, folder_name: str) -> bool:
        created = self._filesystem.create_folder(parent_path, folder_name)
        if created:
            self.update_folder_contents()
            return True
        return False

    @Slot(str, str, result=str)
    def join_paths(self, path1: str, path2: str) -> str:
        return self._filesystem.join(path1, path2)

    def check_and_create_soundtracks(self, emit_signal: bool = True) -> None:
        if not self._output_folder:
            return
        states = self._extractor.album_states(Path(self._output_folder))
        self._album_states.update(states)
        if emit_signal:
            self.albumStateChanged.emit()

    def check_rename_soundtrack(self, album_name: str) -> None:
        if not self._output_folder:
            self.extractionFinished.emit(f"Soundtrack '{album_name}' not found.")
            return
        existing_dir = self._extractor.find_existing_album_dir(Path(self._output_folder), album_name)
        if existing_dir is not None:
            self.extractionFinished.emit(f"Soundtrack '{album_name}' found. Ready to rename.")
        else:
            self.extractionFinished.emit(f"Soundtrack '{album_name}' not found.")

    @Slot(str)
    def extract_soundtrack(self, album_name: str) -> None:
        if not self._output_folder:
            self.extractionFinished.emit("Error: Choose an output folder first")
            return

        language = self._current_language
        include_numbers = self._include_track_numbers
        output_path = Path(self._output_folder)

        # reset cancellation flag and mark extracting
        self._cancel_event.clear()
        self._is_extracting = True
        self.extractionStateChanged.emit(True)

        future = self._executor.submit(
            self._extract_and_rename,
            album_name,
            language,
            include_numbers,
            output_path,
        )
        self._track_future(future)
        future.add_done_callback(
            lambda fut, name=album_name, lang=language, include=include_numbers, target=output_path: self._handle_extract_result(name, lang, include, target, fut)
        )

    def _extract_and_rename(
        self,
        album_name: str,
        language: str,
        include_numbers: bool,
        output_path: Path,
    ) -> dict:
        try:
            success, message = self._extractor.extract_album(
                album_name,
                language,
                include_numbers,
                output_path,
            )
        except Exception as exc:
            import traceback
            error_details = f"Error: {exc}\n{traceback.format_exc()}"
            print(error_details)
            return {"success": False, "message": f"Error during extraction: {exc}", "downloaded": False, "integrity": None}
        if not success:
            return {"success": False, "message": message, "downloaded": False, "integrity": None}

        try:
            rename_success, rename_message = self._extractor.rename_album(
                album_name,
                language,
                include_numbers,
                output_path,
            )
        except Exception as exc:
            import traceback
            print(f"Rename error: {exc}\n{traceback.format_exc()}")
            return {
                "success": False,
                "message": f"Error during rename: {exc}",
                "downloaded": True,
                "integrity": None,
            }
        if not rename_success:
            print(f"Rename failed: {rename_message}")
            return {
                "success": False,
                "message": rename_message or message,
                "downloaded": True,
                "integrity": None,
            }
        final_message = rename_message or message

        integrity_report: AlbumIntegrityReport | None = None
        try:
            integrity_report = self._extractor.verify_album_integrity(
                album_name,
                language,
                include_numbers,
                output_path,
            )
        except Exception as exc:
            import traceback
            print(f"Integrity check error: {exc}\n{traceback.format_exc()}")
            integrity_report = None

        if integrity_report and not integrity_report.complete:
            print(f"Integrity check incomplete: {integrity_report}")
            album_title = ALBUMS.get(album_name, {}).get(language, album_name)
            warning_message = f"{final_message} (Note: Some files may have issues)"
            return {
                "success": True,
                "message": warning_message,
                "downloaded": True,
                "integrity": integrity_report,
            }

        return {
            "success": True,
            "message": final_message,
            "downloaded": True,
            "integrity": integrity_report,
        }

    def _handle_extract_result(self, album_name: str, language: str, include_numbers: bool, output_path: Path, future) -> None:
        try:
            result = future.result()
        except Exception as exc:  # pragma: no cover - safeguard
            result = {"success": False, "message": f"Error: {exc}", "downloaded": False}
        success = bool(result.get("success"))
        message = str(result.get("message", ""))
        integrity = result.get("integrity")
        QTimer.singleShot(
            0,
            lambda: self._finalize_extraction(
                album_name,
                language,
                include_numbers,
                output_path,
                success,
                message,
                integrity,
            ),
        )

    def _finalize_extraction(
        self,
        album_name: str,
        language: str,
        include_numbers: bool,
        output_path: Path,
        success: bool,
        message: str,
        integrity: AlbumIntegrityReport | None,
    ) -> None:
        self._is_extracting = False
        self.extractionStateChanged.emit(False)
        
        existing_dir = self._extractor.find_existing_album_dir(output_path, album_name)
        has_files = existing_dir is not None
        
        self._album_states[album_name] = "rename" if has_files else "extract"
        
        if not message:
            if has_files:
                message = f"Soundtrack '{album_name}' extracted successfully"
            else:
                message = f"Error processing soundtrack '{album_name}'"
        
        if has_files:
            self.coverImageChanged.emit()
            self.update_song_list()
        
        self.albumStateChanged.emit()
        self.canExtractChanged.emit()
        
        QCoreApplication.processEvents()
        
        self.extractionFinished.emit(message)

    def _track_future(self, future):
        self._pending_futures.append(future)

        def _cleanup(completed_future):
            try:
                self._pending_futures.remove(completed_future)
            except ValueError:
                pass

        future.add_done_callback(_cleanup)
        return future

    def _shutdown(self) -> None:
        try:
            self._cancel_event.set()
        except Exception:
            pass
        try:
            self._executor.shutdown(wait=False)
        except Exception:
            pass

    def __del__(self) -> None:
        self._shutdown()

    def _update_extras_album_state(self, album_name: str) -> None:
        target_dir = self._extractor.destination_album_dir(Path(self._output_folder), album_name, self._current_language)
        has_files = target_dir.exists() and any(target_dir.iterdir())
        self._album_states[album_name] = "rename" if has_files else "extract"

    @Slot(result=bool)
    def can_extract(self) -> bool:
        return bool(self._output_folder)

    @Slot(result=str)
    def get_current_album_state(self) -> str:
        return self._album_states.get(self._current_album, "extract")

    def get_resource_path(self, *parts: str) -> str:
        return str(self._locator.resource_path(*parts))

    @Slot(result=bool)
    def check_files_exist(self) -> bool:
        if not self._output_folder:
            return False
        existing_dir = self._extractor.find_existing_album_dir(Path(self._output_folder), self._current_album)
        return existing_dir is not None

    @Slot(result=bool)
    def is_current_album_complete(self) -> bool:
        if not self._output_folder:
            return False
        try:
            report = self._extractor.verify_album_integrity(
                self._current_album,
                self._current_language,
                self._include_track_numbers,
                Path(self._output_folder),
            )
            return bool(report and report.complete)
        except Exception:
            return False

    @Slot(result='QVariantMap')
    def get_current_album_progress(self) -> dict:
        if not self._output_folder:
            return {"expected": 0, "found": 0, "complete": False}
        try:
            expected = self._extractor.expected_track_count(self._current_album, self._current_language)
            found = self._extractor.count_effective_tracks(Path(self._output_folder), self._current_album, self._current_language)
            complete = False
            
            if expected > 0 and found >= expected:
                try:
                    report = self._extractor.verify_album_integrity(
                        self._current_album,
                        self._current_language,
                        self._include_track_numbers,
                        Path(self._output_folder),
                    )
                    complete = bool(report and report.complete)
                except Exception:
                    complete = False
            
            return {"expected": int(expected), "found": int(found), "complete": bool(complete)}
        except Exception:
            return {"expected": 0, "found": 0, "complete": False}

    @Slot()
    def cancel_operations(self) -> None:
        try:
            self._cancel_event.set()
        except Exception:
            pass

    @Slot()
    def sync_with_local_completion(self) -> None:
        """If local files are complete, mark extraction finished and refresh states.

        This is used by the UI poller in remote mode when it detects that all files
        exist and have been renamed, even if the background task has not yet
        propagated completion back to the UI.
        """
        if not self._output_folder:
            return
        try:
            report = self._extractor.verify_album_integrity(
                self._current_album,
                self._current_language,
                self._include_track_numbers,
                Path(self._output_folder),
            )
        except Exception:
            return
        if not report or not report.complete:
            return
        if self._is_extracting:
            self._is_extracting = False
            self.extractionStateChanged.emit(False)
        self._album_states[self._current_album] = "rename"
        self.check_and_create_soundtracks()
        self.albumStateChanged.emit()
        self.coverImageChanged.emit()
        self.update_song_list()

    @Slot(result=str)
    def get_album_path(self) -> str:
        if not self._output_folder:
            return ""
        target = self._extractor.destination_album_dir(Path(self._output_folder), self._current_album, self._current_language)
        return str(target)

    @Slot(str)
    def extraction_finished(self, result: str) -> None:
        self.extractionFinished.emit(result)

    @Property(list, notify=albumsChanged)
    def album_list(self) -> list[str]:
        return list(self.albums.keys())

    @Property(str, notify=coverImageChanged)
    def cover_image(self) -> str:
        if self._config.use_remote and self._r2_client and self._cover_cache:
            manifest = ASSET_MANIFEST.get(self._current_album)
            if manifest:
                cover_rel = manifest.get("cover")
                if cover_rel:
                    try:
                        destination = self._cover_cache._destination_for(cover_rel)
                        if destination.exists():
                            return QUrl.fromLocalFile(str(destination)).toString()
                        self._track_future(self._executor.submit(self._cover_cache.get_cover_path, cover_rel, self._r2_client))
                        return QUrl(self._r2_client.build_url(cover_rel)).toString()
                    except Exception:
                        try:
                            return QUrl(self._r2_client.build_url(cover_rel)).toString()
                        except Exception:
                            return ""
            return ""
        cover_path = self._locator.soundtrack_source_dir(self.albums[self._current_album]["English"]) / "cover.jpg"
        return QUrl.fromLocalFile(str(cover_path)).toString() if cover_path.exists() else ""

    @current_album.setter
    def current_album(self, album: str) -> None:
        if self._current_album == album:
            return
        self._current_album = album
        self.currentAlbumChanged.emit()
        self.coverImageChanged.emit()
        self.albumStateChanged.emit()
        self.update_song_list()

    @Slot(str)
    def set_current_album(self, album: str) -> None:
        self.current_album = album

    @Property(str, notify=currentLanguageChanged)
    def current_language(self) -> str:
        return self._current_language

    @current_language.setter
    def current_language(self, language: str) -> None:
        if self._current_language == language:
            return
        self._current_language = language
        self.currentLanguageChanged.emit()
        self.check_and_create_soundtracks()
        self.albumStateChanged.emit()
        self.update_song_list()

    @Slot(str)
    def set_current_language(self, language: str) -> None:
        self.current_language = language

    @Property('QVariantList', notify=songListChanged)
    def songList(self) -> list[dict[str, str]]:
        return self._song_list

    def update_song_list(self) -> None:
        entries = self._audio_catalog.build(self._current_album, self._current_language)
        self._song_list = []
        for entry in entries:
            if entry.is_remote:
                url = QUrl(entry.source)
            else:
                url = QUrl.fromLocalFile(entry.source)
            self._song_list.append(
                {
                    "title": entry.title,
                    "length": entry.length,
                    "filePath": url.toString(),
                    "isRemote": entry.is_remote,
                    "trackNumber": entry.track_number,
                    "relativePath": entry.relative_path,
                }
            )
        self.songListChanged.emit()

    @Slot(result=str)
    def rename_files(self) -> str:
        if not self._output_folder:
            return "Error: Choose an output folder first"
        success, message = self._extractor.rename_album(
            self._current_album,
            self._current_language,
            self._include_track_numbers,
            Path(self._output_folder),
        )
        if success:
            self.coverImageChanged.emit()
            self._album_states[self._current_album] = "rename"
        return message

    @Property(str, notify=albumsChanged)
    def current_album_title(self) -> str:
        return self.albums[self._current_album][self._current_language]

    @Property(list, notify=albumsChanged)
    def current_track_list(self) -> list[str]:
        return self.albums[self._current_album]["Tracks"][self._current_language]

    @Slot()
    def refresh_album_list(self) -> None:
        self.albumsChanged.emit()

    @Property(bool, notify=None)
    def include_track_numbers(self) -> bool:
        return self._include_track_numbers

    @Slot(bool)
    def set_include_track_numbers(self, value: bool) -> None:
        self._include_track_numbers = value


__all__ = ["RenamerBackend"]
