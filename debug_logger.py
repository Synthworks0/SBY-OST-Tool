import os
import sys
import logging
from datetime import datetime
from PySide6.QtCore import QtMsgType, qInstallMessageHandler

class DebugLogger:
    def __init__(self, debug_enabled=False):
        self.debug_enabled = debug_enabled
        if not debug_enabled:
            return

        # Create logs directory if it doesn't exist
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        logs_dir = os.path.join(base_path, 'logs')
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