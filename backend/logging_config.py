"""
Logging configuration module for ThermosenseIoT Backend.

This module provides centralized logging setup with console and rotating file handlers.
Logging levels and file paths are configurable through the application configuration.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_level: str = "INFO", log_file_path: str = "logs/thermosense.log", 
                  max_bytes: int = 10485760, backup_count: int = 5) -> logging.Logger:
    """
    Configure logging with console and rotating file handlers.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO
        log_file_path: Path to log file. Default: logs/thermosense.log
        max_bytes: Maximum size of log file before rotation (bytes). Default: 10MB (10485760 bytes)
        backup_count: Number of backup files to keep. Default: 5
        
    Returns:
        Configured root logger instance
        
    Requirements:
        - 23.7: Backend service shall write logs to both console and rotating log file
                (max 10MB per file, keep 5 files)
    """
    # Get root logger
    logger = logging.getLogger()
    
    # Clear any existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Set log level from configuration
    log_level_upper = log_level.upper()
    if log_level_upper not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        log_level_upper = "INFO"
        
    logger.setLevel(getattr(logging, log_level_upper))
    
    # Create formatter with detailed format
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler - logs to stdout
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level_upper))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create logs directory if it doesn't exist
    log_file = Path(log_file_path)
    log_dir = log_file.parent
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created log directory: {log_dir}")
    
    # Rotating file handler - logs to file with rotation
    file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level_upper))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Logging configured: level={log_level_upper}, file={log_file_path}, max_size={max_bytes/1024/1024}MB, backups={backup_count}")
    
    return logger
