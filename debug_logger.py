import os
import sys
import logging
import tempfile
import atexit
from datetime import datetime
from PySide6.QtCore import QtMsgType, qInstallMessageHandler

class DebugLogger:
    def __init__(self, debug_enabled=False):
        self.debug_enabled = debug_enabled
        self._qt_prev_handler = None
        self._qt_handler_installed = False
        if not debug_enabled:
            return

        app_name = 'SBY_OST_Tool'
        try:
            if sys.platform == 'darwin':
                # ~/Library/Logs/SBY_OST_Tool
                base_dir = os.path.expanduser('~/Library/Logs')
            elif sys.platform.startswith('win'):
                base_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), app_name)
            else:
                # Linux/Unix: ~/.local/state/SBY_OST_Tool
                base_dir = os.path.expanduser('~/.local/state')
            logs_dir = os.path.join(base_dir, app_name)
            os.makedirs(logs_dir, exist_ok=True)
        except Exception:
            logs_dir = os.path.join(tempfile.gettempdir(), app_name, 'logs')
            os.makedirs(logs_dir, exist_ok=True)

        # Set up logging
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = os.path.join(logs_dir, f'debug_{timestamp}.log')
        
        self.logger = logging.getLogger('AppLogger')
        self.logger.setLevel(logging.DEBUG)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)

        # Install Qt message handler safely. On macOS frozen builds this can crash at teardown
        # when Qt emits messages after Python finalization. Allow opt-in via env, otherwise
        # install for other platforms.
        install_qt_handler = os.environ.get('APP_ENABLE_QT_LOGGING') == '1'
        if not (sys.platform == 'darwin' and getattr(sys, 'frozen', False)):
            install_qt_handler = True

        if install_qt_handler:
            def qt_message_handler(msg_type, context, message):
                try:
                    level_map = {
                        QtMsgType.QtDebugMsg: self.debug,
                        QtMsgType.QtInfoMsg: self.info,
                        QtMsgType.QtWarningMsg: self.warning,
                        QtMsgType.QtCriticalMsg: self.error,
                        QtMsgType.QtFatalMsg: self.error
                    }
                    log_func = level_map.get(msg_type, self.info)
                    file_info = f"{getattr(context, 'file', None)}:{getattr(context, 'line', None)}"
                    log_func(f"[QML] {file_info} - {message}")
                except Exception:
                    pass

            try:
                self._qt_prev_handler = qInstallMessageHandler(qt_message_handler)
                self._qt_handler_installed = True
            except Exception:
                self._qt_prev_handler = None
                self._qt_handler_installed = False

        def _restore_qt_handler():
            try:
                if self._qt_handler_installed:
                    qInstallMessageHandler(self._qt_prev_handler)
                    self._qt_handler_installed = False
            except Exception:
                pass
        atexit.register(_restore_qt_handler)

    def debug(self, message):
        if self.debug_enabled:
            self.logger.debug(message)

    def info(self, message):
        if self.debug_enabled:
            self.logger.info(message)

    def warning(self, message):
        if self.debug_enabled:
            self.logger.warning(message)

    def error(self, message):
        if self.debug_enabled:
            self.logger.error(message)