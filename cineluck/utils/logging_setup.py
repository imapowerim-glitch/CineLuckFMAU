"""
Logging setup for CineLuck
Configures structured logging with file rotation and filtering
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


class RotatingFileHandlerWithLines(logging.handlers.RotatingFileHandler):
    """Custom rotating file handler that keeps last N lines instead of file size"""
    
    def __init__(self, filename, max_lines=100, encoding=None):
        super().__init__(filename, maxBytes=0, backupCount=0, encoding=encoding)
        self.max_lines = max_lines
    
    def shouldRollover(self, record):
        """Check if we should roll over based on line count"""
        if self.stream is None:
            self.stream = self._open()
        
        try:
            # Count lines in current file
            with open(self.baseFilename, 'r', encoding=self.encoding) as f:
                line_count = sum(1 for _ in f)
            return line_count >= self.max_lines
        except:
            return False
    
    def doRollover(self):
        """Perform rollover by keeping only the last N lines"""
        if self.stream:
            self.stream.close()
            self.stream = None
        
        try:
            # Read all lines
            with open(self.baseFilename, 'r', encoding=self.encoding) as f:
                lines = f.readlines()
            
            # Keep only the last max_lines
            if len(lines) > self.max_lines:
                lines = lines[-self.max_lines:]
            
            # Write back
            with open(self.baseFilename, 'w', encoding=self.encoding) as f:
                f.writelines(lines)
        except Exception:
            pass  # If rollover fails, just continue
        
        if not self.delay:
            self.stream = self._open()


def setup_logging(log_file: Optional[Path] = None, level: str = "INFO"):
    """
    Set up logging configuration for CineLuck
    
    Args:
        log_file: Path to log file (optional)
        level: Logging level
    """
    # Clear any existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Set logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if log file provided)
    if log_file:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandlerWithLines(
                str(log_file), 
                max_lines=100,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            # If file logging fails, log to console
            console_handler.emit(
                logging.LogRecord(
                    "setup_logging", logging.WARNING, __file__, 0,
                    f"Failed to set up file logging: {e}", (), None
                )
            )
    
    # Set specific logger levels
    logging.getLogger('picamera2').setLevel(logging.WARNING)
    logging.getLogger('libcamera').setLevel(logging.WARNING)
    logging.getLogger('PyQt6').setLevel(logging.WARNING)
    
    # Log the setup completion
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {level}, File: {log_file}")