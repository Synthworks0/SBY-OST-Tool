from __future__ import annotations
import multiprocessing
import os
import sys
from soundtrack_tool.environment import configure_qt_environment

configure_qt_environment()

import resources_rc  # noqa: E402
from PySide6.QtCore import QLibraryInfo, QUrl  # noqa: E402
from PySide6.QtGui import QIcon  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from debug_logger import DebugLogger  # noqa: E402
from soundtrack_tool.backend import RenamerBackend  # noqa: E402
from soundtrack_tool.resources import ResourceLocator  # noqa: E402


DEBUG_MODE = os.environ.get("SBY_DEBUG", "").lower() in ("1", "true", "yes")
debug_logger = DebugLogger(DEBUG_MODE)


def _log_qt_environment(app: QApplication) -> None:
    if not DEBUG_MODE:
        return
    try:
        debug_logger.info(f"Qt library paths: {app.libraryPaths()}")
        debug_logger.info(f"QLibraryInfo PluginsPath: {QLibraryInfo.path(QLibraryInfo.PluginsPath)}")
        debug_logger.info(f"QLibraryInfo LibraryExecutablesPath: {QLibraryInfo.path(QLibraryInfo.LibraryExecutablesPath)}")
        debug_logger.info(f"QLibraryInfo QmlImportsPath: {QLibraryInfo.path(QLibraryInfo.QmlImportsPath)}")
        debug_logger.info(f"QLibraryInfo LibrariesPath: {QLibraryInfo.path(QLibraryInfo.LibrariesPath)}")
    except Exception as exc:  # pragma: no cover - logging helper
        debug_logger.warning(f"Failed to query QLibraryInfo paths: {exc}")

def _add_plugin_paths(app: QApplication, locator: ResourceLocator) -> None:
    if not getattr(sys, "frozen", False):
        return
    plugin_candidates = [
        locator.runtime_root / "PySide6" / "Qt" / "plugins",
        locator.runtime_root / "Qt" / "plugins",
        locator.runtime_root / "plugins",
        locator.app_resources_dir / "PySide6" / "Qt" / "plugins",
        locator.app_resources_dir / "Qt" / "plugins",
        locator.app_resources_dir / "plugins",
    ]
    for candidate in plugin_candidates:
        if candidate.is_dir():
            app.addLibraryPath(str(candidate))
            if DEBUG_MODE:
                debug_logger.info(f"Added plugin path: {candidate}")

    if sys.platform == "darwin":
        multimedia_dirs = [path / "multimedia" for path in plugin_candidates if path.is_dir()]
        ffmpeg_plugins = {
            "libqtmedia_ffmpeg.dylib",
            "libqffmpegmediaplugin.dylib",
            "libffmpegmediaplugin.dylib",
            "ffmpegmediaplugin.dylib",
        }
        ffmpeg_present = any((directory / name).exists() for directory in multimedia_dirs for name in ffmpeg_plugins)
        if not ffmpeg_present:
            os.environ["QT_MEDIA_BACKEND"] = "darwin"
            if DEBUG_MODE:
                debug_logger.info("FFmpeg multimedia plugin not found; forcing QT_MEDIA_BACKEND=darwin")

def _load_qml(engine: QQmlApplicationEngine, locator: ResourceLocator) -> None:
    for import_path in [
        locator.runtime_root / "PySide6" / "Qt" / "qml",
        locator.app_resources_dir / "PySide6" / "Qt" / "qml",
    ]:
        if import_path.is_dir():
            engine.addImportPath(str(import_path))
            if DEBUG_MODE:
                debug_logger.info(f"Added QML import path: {import_path}")

    qml_candidates = locator.qml_search_candidates()
    qml_path = next((path for path in qml_candidates if path.exists()), qml_candidates[0])
    debug_logger.info(f"Loading QML file: {qml_path}")
    engine.load(QUrl.fromLocalFile(str(qml_path)))
    try:
        for warning in engine.warnings():
            debug_logger.warning(str(warning))
    except Exception:
        pass

def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    if DEBUG_MODE:
        os.environ.setdefault("QML_DEBUG_MESSAGES", "1")
        debug_logger.info("Starting GUI application")

    locator = ResourceLocator()
    _add_plugin_paths(app, locator)
    _log_qt_environment(app)

    if sys.platform.startswith('linux'):
        from PySide6.QtGui import QFontDatabase
        from pathlib import Path
        
        if getattr(sys, 'frozen', False):
            fonts_dir = Path(sys._MEIPASS) / 'resources' / 'fonts'
        else:
            fonts_dir = Path(__file__).parent / 'resources' / 'fonts'
        
        if fonts_dir.exists():
            for font_file in fonts_dir.glob('*.otf'):
                font_id = QFontDatabase.addApplicationFont(str(font_file))
                if font_id != -1:
                    debug_logger.info(f"Loaded font: {font_file.name}")

    engine = QQmlApplicationEngine()
    renamer = RenamerBackend()
    engine.rootContext().setContextProperty("renamer", renamer)
    _load_qml(engine, locator)

    if not engine.rootObjects():
        debug_logger.error("Failed to load QML - no root objects")
        return -1

    icon_path = locator.application_icon_path()
    icon = QIcon(str(icon_path))
    
    if str(icon_path).endswith('.png'):
        from PySide6.QtGui import QPixmap
        from PySide6.QtCore import Qt
        for size in [16, 32, 48, 64, 128]:
            pixmap = QPixmap(str(icon_path)).scaled(
                size, size, 
                Qt.AspectRatioMode.KeepAspectRatio, 
                Qt.TransformationMode.SmoothTransformation
            )
            if not pixmap.isNull():
                icon.addPixmap(pixmap)
    
    app.setWindowIcon(icon)
    
    if sys.platform.startswith('linux'):
        app.setDesktopFileName("SBY_OST_Tool")

    window = engine.rootObjects()[0]
    
    if hasattr(window, 'setIcon'):
        window.setIcon(icon)

    return app.exec()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    sys.exit(main())
