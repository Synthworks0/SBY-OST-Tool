import os
import sys
import logging
import tempfile
from datetime import datetime
from PySide6.QtCore import QtMsgType, qInstallMessageHandler

class DebugLogger:
    def __init__(self, debug_enabled=False):
        self.debug_enabled = debug_enabled
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

        # Install Qt message handler
        def qt_message_handler(msg_type, context, message):
            level_map = {
                QtMsgType.QtDebugMsg: self.debug,
                QtMsgType.QtInfoMsg: self.info,
                QtMsgType.QtWarningMsg: self.warning,
                QtMsgType.QtCriticalMsg: self.error,
                QtMsgType.QtFatalMsg: self.error
            }
            
            log_func = level_map.get(msg_type, self.info)
            file_info = f"{context.file}:{context.line}" if hasattr(context, 'file') else "Unknown location"
            log_func(f"[QML] {file_info} - {message}")

        qInstallMessageHandler(qt_message_handler)

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