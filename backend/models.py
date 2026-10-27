"""
Pydantic data models for the ThermosenseIoT Dashboard backend service.

These models provide request/response validation and API documentation for:
- Temperature readings from MQTT sensors
- Alert events for threshold violations
- Configuration updates for threshold management
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator, ConfigDict


class TemperatureReading(BaseModel):
    """
    Temperature reading data structure from sensor devices.
    
    Validates sensor data against business rules:
    - Temperature within physical range (-50°C to 150°C)
    - Device ID length constraints
    - Standard temperature unit notation
    - ISO 8601 timestamp format
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "device_id": "sensor-001",
                    "temperature": 25.3,
                    "unit": "C",
                    "timestamp": "2024-01-15T10:30:45Z"
                }
            ]
        }
    )
    
    device_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for the sensor device",
        examples=["sensor-001"]
    )
    
    temperature: float = Field(
        ...,
        ge=-50.0,
        le=150.0,
        description="Temperature value in specified unit",
        examples=[25.3]
    )
    
    unit: Literal["C", "F", "K"] = Field(
        ...,
        description="Temperature unit: Celsius (C), Fahrenheit (F), or Kelvin (K)",
        examples=["C"]
    )
    
    timestamp: str = Field(
        ...,
        description="ISO 8601 formatted timestamp",
        examples=["2024-01-15T10:30:45Z"]
    )
    
    @field_validator("timestamp")
    @classmethod
    def validate_iso8601_timestamp(cls, v: str) -> str:
        """
        Validate that timestamp is in valid ISO 8601 format.
        
        Accepts formats with or without 'Z' suffix:
        - 2024-01-15T10:30:45Z
        - 2024-01-15T10:30:45+00:00
        - 2024-01-15T10:30:45.123456Z
        
        Raises:
            ValueError: If timestamp format is invalid
        """
        try:
            # Try parsing with 'Z' suffix
            if v.endswith('Z'):
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            else:
                datetime.fromisoformat(v)
            return v
        except ValueError as e:
            raise ValueError(
                f"Invalid ISO 8601 timestamp format: {v}. "
                f"Expected format: YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+00:00"
            ) from e


class AlertEvent(BaseModel):
    """
    Alert event triggered when temperature exceeds or falls below threshold.
    
    Tracks threshold violations with full context:
    - Which device triggered the alert
    - The temperature value that violated the threshold
    - The threshold value at the time of alert
    - Alert type classification
    - Resolution status for alert lifecycle management
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "device_id": "sensor-001",
                    "temperature": 37.5,
                    "threshold": 35.0,
                    "alert_type": "high_temperature",
                    "timestamp": "2024-01-15T10:35:12Z",
                    "resolved": False
                }
            ]
        }
    )
    
    device_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Device that triggered the alert",
        examples=["sensor-001"]
    )
    
    temperature: float = Field(
        ...,
        ge=-50.0,
        le=150.0,
        description="Temperature value that triggered the alert",
        examples=[37.5]
    )
    
    threshold: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Threshold value at the time of alert",
        examples=[35.0]
    )
    
    alert_type: str = Field(
        ...,
        description="Type of alert (e.g., 'high_temperature')",
        examples=["high_temperature"]
    )
    
    timestamp: str = Field(
        ...,
        description="ISO 8601 formatted timestamp when alert was created",
        examples=["2024-01-15T10:35:12Z"]
    )
    
    resolved: bool = Field(
        default=False,
        description="Whether the alert has been resolved (temperature returned to normal)"
    )
    
    @field_validator("timestamp")
    @classmethod
    def validate_iso8601_timestamp(cls, v: str) -> str:
        """
        Validate that timestamp is in valid ISO 8601 format.
        
        Raises:
            ValueError: If timestamp format is invalid
        """
        try:
            if v.endswith('Z'):
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            else:
                datetime.fromisoformat(v)
            return v
        except ValueError as e:
            raise ValueError(
                f"Invalid ISO 8601 timestamp format: {v}. "
                f"Expected format: YYYY-MM-DDTHH:MM:SSZ or YYYY-MM-DDTHH:MM:SS+00:00"
            ) from e


class ConfigUpdate(BaseModel):
    """
    Configuration update model for temperature threshold management.
    
    Enforces business rules for threshold values:
    - Must be within operational range (0°C to 100°C)
    - Provides API documentation for configuration endpoint
    """
    
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "threshold": 35.0
                }
            ]
        }
    )
    
    threshold: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Temperature threshold value in Celsius (0 to 100)",
        examples=[35.0]
    )
