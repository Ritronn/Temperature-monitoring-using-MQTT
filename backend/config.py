"""
Configuration module for ThermosenseIoT Backend Service.

This module provides functions to load, validate, and save configuration from config.json.
It supports environment variable overrides for key settings and creates default configuration
when the file doesn't exist.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict


# Default configuration values
DEFAULT_CONFIG = {
    "mqtt_broker_host": "localhost",
    "mqtt_broker_port": 1883,
    "default_threshold": 35.0,
    "database_path": "thermosense.db",
    "websocket_port": 8000,
    "sensor": {
        "device_id": "sensor-001",
        "publish_interval": 2.0,
        "temperature_min": 20.0,
        "temperature_max": 32.0
    },
    "logging": {
        "level": "INFO",
        "file_path": "logs/thermosense.log",
        "max_bytes": 10485760,
        "backup_count": 5
    },
    "smtp": {
        "enabled": True,
        "host": "smtp.gmail.com",
        "port": 587,
        "user": "gojoritron@gmail.com",
        "password": "zvgtzzrwkztumdwk",
        "recipient": "rutvikkale2006@gmail.com",
        "use_tls": True
    }
}

# Required configuration fields
REQUIRED_FIELDS = [
    "mqtt_broker_host",
    "mqtt_broker_port",
    "default_threshold",
    "database_path"
]


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """
    Load and validate configuration from JSON file.
    
    If the configuration file doesn't exist, creates it with default values.
    Applies environment variable overrides for key settings after loading.
    
    Args:
        config_path: Path to the configuration file (default: "config.json")
        
    Returns:
        Dictionary containing validated configuration
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    config_file = Path(config_path)
    
    # Create default configuration if file doesn't exist
    if not config_file.exists():
        print(f"Configuration file {config_path} not found. Creating with default values.")
        save_config_to_file(DEFAULT_CONFIG, config_path)
        config = DEFAULT_CONFIG.copy()
    else:
        # Load existing configuration
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Error reading configuration file: {e}")
    
    # Validate required fields
    _validate_config(config)
    
    # Apply environment variable overrides
    config = _apply_env_overrides(config)
    
    return config


def _validate_config(config: Dict[str, Any]) -> None:
    """
    Validate that all required configuration fields are present and valid.
    
    Args:
        config: Configuration dictionary to validate
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    # Check required fields exist
    for field in REQUIRED_FIELDS:
        if field not in config:
            raise ValueError(f"Required configuration field '{field}' is missing")
    
    # Validate mqtt_broker_host
    if not isinstance(config["mqtt_broker_host"], str) or not config["mqtt_broker_host"]:
        raise ValueError("mqtt_broker_host must be a non-empty string")
    
    # Validate mqtt_broker_port
    if not isinstance(config["mqtt_broker_port"], int):
        raise ValueError("mqtt_broker_port must be an integer")
    if not (1 <= config["mqtt_broker_port"] <= 65535):
        raise ValueError("mqtt_broker_port must be between 1 and 65535")
    
    # Validate default_threshold
    if not isinstance(config["default_threshold"], (int, float)):
        raise ValueError("default_threshold must be a number")
    if not (0.0 <= config["default_threshold"] <= 100.0):
        raise ValueError("default_threshold must be between 0.0 and 100.0")
    
    # Validate database_path
    if not isinstance(config["database_path"], str) or not config["database_path"]:
        raise ValueError("database_path must be a non-empty string")


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply environment variable overrides to configuration.
    
    Supported environment variables:
    - MQTT_BROKER_HOST: Override mqtt_broker_host
    - MQTT_BROKER_PORT: Override mqtt_broker_port
    - DEFAULT_THRESHOLD: Override default_threshold
    - DATABASE_PATH: Override database_path
    - WEBSOCKET_PORT: Override websocket_port
    
    Args:
        config: Base configuration dictionary
        
    Returns:
        Configuration dictionary with environment overrides applied
    """
    config = config.copy()
    
    # Override mqtt_broker_host
    if "MQTT_BROKER_HOST" in os.environ:
        config["mqtt_broker_host"] = os.environ["MQTT_BROKER_HOST"]
    
    # Override mqtt_broker_port
    if "MQTT_BROKER_PORT" in os.environ:
        try:
            config["mqtt_broker_port"] = int(os.environ["MQTT_BROKER_PORT"])
        except ValueError:
            print(f"Warning: Invalid MQTT_BROKER_PORT environment variable, using config value")
    
    # Override default_threshold
    if "DEFAULT_THRESHOLD" in os.environ:
        try:
            config["default_threshold"] = float(os.environ["DEFAULT_THRESHOLD"])
        except ValueError:
            print(f"Warning: Invalid DEFAULT_THRESHOLD environment variable, using config value")
    
    # Override database_path
    if "DATABASE_PATH" in os.environ:
        config["database_path"] = os.environ["DATABASE_PATH"]
    
    # Override websocket_port
    if "WEBSOCKET_PORT" in os.environ:
        try:
            config["websocket_port"] = int(os.environ["WEBSOCKET_PORT"])
        except ValueError:
            print(f"Warning: Invalid WEBSOCKET_PORT environment variable, using config value")
    
    # Override SMTP settings
    smtp = config.get("smtp", {}).copy()
    if "SMTP_USER" in os.environ:
        smtp["user"] = os.environ["SMTP_USER"]
    if "SMTP_PASS" in os.environ:
        smtp["password"] = os.environ["SMTP_PASS"]
    if "SMTP_HOST" in os.environ:
        smtp["host"] = os.environ["SMTP_HOST"]
    if "SMTP_PORT" in os.environ:
        try:
            smtp["port"] = int(os.environ["SMTP_PORT"])
        except ValueError:
            print("Warning: Invalid SMTP_PORT environment variable, using config value")
    if "SMTP_RECIPIENT" in os.environ:
        smtp["recipient"] = os.environ["SMTP_RECIPIENT"]
    if "SMTP_ENABLED" in os.environ:
        smtp["enabled"] = os.environ["SMTP_ENABLED"].lower() in ("true", "1", "yes")
    config["smtp"] = smtp
    
    return config


def save_config_to_file(config: Dict[str, Any], config_path: str = "config.json") -> None:
    """
    Persist configuration changes to JSON file.
    
    Args:
        config: Configuration dictionary to save
        config_path: Path to the configuration file (default: "config.json")
        
    Raises:
        ValueError: If configuration is invalid
        IOError: If file cannot be written
    """
    # Validate before saving
    _validate_config(config)
    
    config_file = Path(config_path)
    
    try:
        # Create parent directory if it doesn't exist
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write configuration with nice formatting
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"Configuration saved to {config_path}")
        
    except Exception as e:
        raise IOError(f"Error writing configuration file: {e}")


def update_config_field(field: str, value: Any, config_path: str = "config.json") -> Dict[str, Any]:
    """
    Update a single configuration field and save to file.
    
    Args:
        field: Configuration field name to update
        value: New value for the field
        config_path: Path to the configuration file (default: "config.json")
        
    Returns:
        Updated configuration dictionary
        
    Raises:
        ValueError: If field or value is invalid
    """
    # Load current configuration
    config = load_config(config_path)
    
    # Update field
    config[field] = value
    
    # Validate and save
    save_config_to_file(config, config_path)
    
    return config
