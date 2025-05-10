"""
Logging configuration module
Sets up logging for the application
"""
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional


class LoggerSetup:
    def __init__(self,
                 name: str = 'PingMonitor',
                 max_bytes: int = 1024 * 1024,  # 1 MB
                 backup_count: int = 5):
        self.logger: Optional[logging.Logger] = None
        self.name = name
        self.max_bytes = max_bytes
        self.backup_count = backup_count

    def setup(self) -> logging.Logger:
        """Configure and return logger instance"""
        if self.logger is not None:
            return self.logger

        # Create logger
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Setup file handler
        log_dir = os.path.expanduser('~')
        log_file = os.path.join(log_dir, 'ping_monitor.log')

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)

        # Setup console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)

        # Add handlers if they haven't been added already
        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        self.logger = logger
        return logger

    def get_logger(self) -> logging.Logger:
        """Get or create logger instance"""
        if self.logger is None:
            return self.setup()
        return self.logger
