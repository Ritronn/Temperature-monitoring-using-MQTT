# Logging Configuration Module

## Overview

The `logging_config.py` module provides centralized logging configuration for the ThermosenseIoT backend service. It implements dual-output logging (console and rotating file) as specified in Requirements 23.7.

## Features

- **Console Logging**: Real-time log output to stdout for development and monitoring
- **Rotating File Logging**: Persistent logs with automatic rotation to prevent disk space issues
- **Configurable Log Levels**: Support for DEBUG, INFO, WARNING, ERROR, and CRITICAL levels
- **Automatic Directory Creation**: Creates log directory if it doesn't exist
- **Structured Format**: Consistent timestamp, logger name, level, and message format

## Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `log_level` | str | "INFO" | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `log_file_path` | str | "logs/thermosense.log" | Path to the log file |
| `max_bytes` | int | 10485760 | Maximum log file size before rotation (10MB) |
| `backup_count` | int | 5 | Number of backup files to keep |

## Usage

### Basic Usage

```python
from logging_config import setup_logging
import logging

# Setup logging with defaults
setup_logging()

# Get logger and use it
logger = logging.getLogger(__name__)
logger.info("Application started")
logger.warning("Temperature threshold exceeded")
logger.error("Database connection failed", exc_info=True)
```

### With Configuration File

```python
import json
import logging
from logging_config import setup_logging

# Load configuration from config.json
with open('config.json', 'r') as f:
    config = json.load(f)

logging_config = config.get("logging", {})

# Setup logging from configuration
setup_logging(
    log_level=logging_config.get("level", "INFO"),
    log_file_path=logging_config.get("file_path", "logs/thermosense.log"),
    max_bytes=logging_config.get("max_bytes", 10485760),
    backup_count=logging_config.get("backup_count", 5)
)

logger = logging.getLogger(__name__)
logger.info("Configured from config.json")
```

### Custom Configuration

```python
from logging_config import setup_logging
import logging

# Custom configuration for development
setup_logging(
    log_level="DEBUG",
    log_file_path="logs/development.log",
    max_bytes=5242880,  # 5MB
    backup_count=3
)

logger = logging.getLogger(__name__)
logger.debug("Debug information")
```

## Log File Rotation

The rotating file handler automatically manages log files:

- When `thermosense.log` reaches 10MB, it's renamed to `thermosense.log.1`
- Previous backups are shifted: `thermosense.log.1` → `thermosense.log.2`, etc.
- The oldest backup beyond `backup_count` is deleted
- A new `thermosense.log` file is created

Example rotation sequence:
```
thermosense.log       (current, active)
thermosense.log.1     (most recent backup)
thermosense.log.2
thermosense.log.3
thermosense.log.4
thermosense.log.5     (oldest backup)
```

## Log Format

All log messages follow this format:
```
YYYY-MM-DD HH:MM:SS - logger_name - LEVEL - message
```

Example:
```
2026-10-26 22:04:48 - backend.mqtt_client - INFO - Connected to MQTT broker at localhost:1883
2026-10-26 22:04:49 - backend.mqtt_client - WARNING - Temperature threshold exceeded: 37.5°C > 35.0°C
2026-10-26 22:04:50 - backend.database - ERROR - Database write failed
```

## Integration with Main Application

The logging module should be initialized once at application startup, typically in `main.py`:

```python
from logging_config import setup_logging
from config import load_config
import logging

# Application startup
config = load_config()
setup_logging(
    log_level=config["logging"]["level"],
    log_file_path=config["logging"]["file_path"],
    max_bytes=config["logging"]["max_bytes"],
    backup_count=config["logging"]["backup_count"]
)

logger = logging.getLogger(__name__)
logger.info("ThermosenseIoT Backend Service started")
```

## Requirements Mapping

This module satisfies the following requirements:

- **Requirement 23.7**: Backend service shall write logs to both console and a rotating log file (max 10MB per file, keep 5 files)
- **Requirement 23.1**: Log MQTT connection events at INFO level
- **Requirement 23.2**: Log incoming MQTT messages at DEBUG level
- **Requirement 23.3**: Log Alert_Events at WARNING level
- **Requirement 23.4**: Log HTTP API requests at INFO level
- **Requirement 23.5**: Log Sensor_Simulator publishing events at INFO level
- **Requirement 23.6**: Log errors with stack traces at ERROR level

## Notes

- The logger uses UTF-8 encoding for the log file to properly handle special characters (e.g., °C)
- The `setup_logging()` function clears any existing handlers to prevent duplicate log messages
- Call `setup_logging()` only once at application startup
- Use `logging.getLogger(__name__)` in each module to get a module-specific logger
