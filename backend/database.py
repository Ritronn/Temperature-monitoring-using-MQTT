"""
Database manager module for ThermosenseIoT Backend Service.

This module provides the DatabaseManager class for handling all database operations,
including schema creation, data persistence, and queries for temperature readings
and alert events.
"""

import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any


# Database schema SQL
SCHEMA_SQL = """
-- Temperature readings table
CREATE TABLE IF NOT EXISTS temperature_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    temperature REAL NOT NULL,
    unit TEXT NOT NULL,
    timestamp TEXT NOT NULL
);

-- Indexes for temperature_readings
CREATE INDEX IF NOT EXISTS idx_timestamp ON temperature_readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_device_timestamp ON temperature_readings(device_id, timestamp);

-- Alert events table
CREATE TABLE IF NOT EXISTS alert_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    temperature REAL NOT NULL,
    threshold REAL NOT NULL,
    alert_type TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    resolved BOOLEAN NOT NULL DEFAULT 0
);

-- Indexes for alert_events
CREATE INDEX IF NOT EXISTS idx_alert_timestamp ON alert_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_alert_resolved ON alert_events(resolved);
CREATE INDEX IF NOT EXISTS idx_alert_device_resolved ON alert_events(device_id, resolved);
"""


class DatabaseManager:
    """
    Manages SQLite database operations for temperature readings and alert events.
    
    This class handles database initialization, schema creation, and provides methods
    for inserting and querying temperature data and alerts. The database connection
    is configured with check_same_thread=False to allow usage from multiple threads
    (MQTT thread and FastAPI async threads).
    
    Attributes:
        db_path (str): Path to the SQLite database file
        connection (sqlite3.Connection): Active database connection
    """
    
    def __init__(self, db_path: str):
        """
        Initialize the DatabaseManager with the specified database path.
        
        Creates the database file and initializes the schema if it doesn't exist.
        Configures the connection for thread-safe operation.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self._initialize_db()
    
    def _initialize_db(self) -> None:
        """
        Initialize the database connection and create schema if needed.
        
        Creates the database file if it doesn't exist, establishes a connection
        with check_same_thread=False for thread safety, and executes the schema
        creation SQL to ensure all tables and indexes exist.
        
        The connection uses Row factory to enable dictionary-like access to
        query results.
        """
        # Ensure parent directory exists
        db_file = Path(self.db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create connection with thread-safe configuration
        self.connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False
        )
        
        # Enable Row factory for dictionary-like access
        self.connection.row_factory = sqlite3.Row
        
        # Execute schema creation SQL
        cursor = self.connection.cursor()
        cursor.executescript(SCHEMA_SQL)
        self.connection.commit()
        
        print(f"Database initialized at {self.db_path}")
    
    def insert_reading(self, reading) -> None:
        """
        Insert a temperature reading into the database.
        
        Uses parameterized queries to prevent SQL injection. The reading parameter
        should be a TemperatureReading Pydantic model or dictionary with the
        required fields: device_id, temperature, unit, timestamp.
        
        Args:
            reading: TemperatureReading object or dict with device_id, temperature, unit, timestamp
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO temperature_readings (device_id, temperature, unit, timestamp)
            VALUES (?, ?, ?, ?)
            """,
            (
                reading.device_id if hasattr(reading, 'device_id') else reading['device_id'],
                reading.temperature if hasattr(reading, 'temperature') else reading['temperature'],
                reading.unit if hasattr(reading, 'unit') else reading['unit'],
                reading.timestamp if hasattr(reading, 'timestamp') else reading['timestamp']
            )
        )
        self.connection.commit()
    
    def insert_alert(self, alert) -> None:
        """
        Insert an alert event into the database with duplicate checking.
        
        Before inserting a new alert, this method checks if an unresolved alert
        already exists for the device. If an unresolved alert exists, the new
        alert is not created (prevents duplicate alerts per device).
        
        Uses parameterized queries to prevent SQL injection. The alert parameter
        should be an AlertEvent Pydantic model or dictionary with the required
        fields: device_id, temperature, threshold, alert_type, timestamp, resolved.
        
        Args:
            alert: AlertEvent object or dict with device_id, temperature, threshold,
                   alert_type, timestamp, resolved fields
        """
        # Extract device_id from alert
        device_id = alert.device_id if hasattr(alert, 'device_id') else alert['device_id']
        
        # Check if unresolved alert already exists for this device
        cursor = self.connection.cursor()
        cursor.execute(
            """
            SELECT id FROM alert_events
            WHERE device_id = ? AND resolved = 0
            """,
            (device_id,)
        )
        existing = cursor.fetchone()
        
        if existing:
            # Don't create duplicate alert - an unresolved alert already exists
            return
        
        # Insert new alert
        cursor.execute(
            """
            INSERT INTO alert_events 
            (device_id, temperature, threshold, alert_type, timestamp, resolved)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                device_id,
                alert.temperature if hasattr(alert, 'temperature') else alert['temperature'],
                alert.threshold if hasattr(alert, 'threshold') else alert['threshold'],
                alert.alert_type if hasattr(alert, 'alert_type') else alert['alert_type'],
                alert.timestamp if hasattr(alert, 'timestamp') else alert['timestamp'],
                0 if (hasattr(alert, 'resolved') and not alert.resolved) or (not hasattr(alert, 'resolved') and not alert.get('resolved', False)) else 1
            )
        )
        self.connection.commit()
    
    def resolve_alerts(self, device_id: str) -> None:
        """
        Mark all unresolved alerts for a device as resolved.
        
        This method is called when temperature returns to normal (below threshold)
        to mark any active alerts for the device as resolved. Uses parameterized
        query to prevent SQL injection.
        
        Args:
            device_id: The device identifier whose alerts should be resolved
        """
        cursor = self.connection.cursor()
        cursor.execute(
            """
            UPDATE alert_events
            SET resolved = 1
            WHERE device_id = ? AND resolved = 0
            """,
            (device_id,)
        )
        self.connection.commit()
    
    def cleanup_old_readings(self, days: int = 7) -> None:
        """
        Delete temperature readings older than the specified number of days.
        
        This method implements the data retention policy by removing old readings
        from the database to prevent unbounded growth. The cutoff timestamp is
        calculated as UTC now minus the retention period, and all readings with
        timestamps before the cutoff are deleted.
        
        Args:
            days: Number of days to retain readings (default: 7)
        
        Example:
            db.cleanup_old_readings(days=7)  # Remove readings older than 7 days
        """
        from datetime import datetime, timedelta
        
        # Calculate cutoff timestamp (UTC now - retention period)
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
        
        # Execute parameterized delete query
        cursor = self.connection.cursor()
        cursor.execute(
            """
            DELETE FROM temperature_readings
            WHERE timestamp < ?
            """,
            (cutoff,)
        )
        deleted_count = cursor.rowcount
        self.connection.commit()
        
        print(f"Cleaned up {deleted_count} readings older than {days} days (cutoff: {cutoff})")
    
    def get_readings_history(
        self,
        start_time: str,
        end_time: str,
        device_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Query temperature readings within a time range.
        
        Retrieves all temperature readings between start_time and end_time,
        optionally filtered by device_id. Uses indexed queries for performance.
        Results are ordered by timestamp in ascending order (oldest first).
        
        Args:
            start_time: ISO 8601 formatted timestamp for range start (inclusive)
            end_time: ISO 8601 formatted timestamp for range end (inclusive)
            device_id: Optional device ID to filter results
            
        Returns:
            List of dictionaries containing temperature reading records
        """
        cursor = self.connection.cursor()
        
        if device_id:
            # Use idx_device_timestamp index for filtering by device and time
            cursor.execute(
                """
                SELECT * FROM temperature_readings
                WHERE timestamp >= ? AND timestamp <= ? AND device_id = ?
                ORDER BY timestamp ASC
                """,
                (start_time, end_time, device_id)
            )
        else:
            # Use idx_timestamp index for time range query
            cursor.execute(
                """
                SELECT * FROM temperature_readings
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
                """,
                (start_time, end_time)
            )
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_latest_readings(self) -> List[Dict[str, Any]]:
        """
        Fetch the most recent temperature reading for each device.
        
        Returns one reading per unique device_id, selecting the reading with
        the most recent timestamp for each device. Useful for displaying
        current status across all sensors.
        
        Returns:
            List of dictionaries containing the latest reading for each device
        """
        cursor = self.connection.cursor()
        
        # First get all unique device IDs
        cursor.execute(
            """
            SELECT DISTINCT device_id FROM temperature_readings
            """
        )
        devices = [row[0] for row in cursor.fetchall()]
        
        # Fetch latest reading for each device
        latest = []
        for device_id in devices:
            cursor.execute(
                """
                SELECT * FROM temperature_readings
                WHERE device_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (device_id,)
            )
            row = cursor.fetchone()
            if row:
                latest.append(dict(row))
        
        return latest
    
    def get_alerts(self, resolved: Optional[bool] = None) -> List[Dict[str, Any]]:
        """
        Query alert events with optional filtering by resolution status.
        
        Retrieves alert events, optionally filtered by whether they have been
        resolved. Uses indexes for efficient querying. Results are ordered by
        timestamp in descending order (most recent first).
        
        Args:
            resolved: Optional filter - True for resolved alerts, False for
                     unresolved alerts, None for all alerts
                     
        Returns:
            List of dictionaries containing alert event records
        """
        cursor = self.connection.cursor()
        
        if resolved is not None:
            # Use idx_alert_resolved index for filtering by resolution status
            cursor.execute(
                """
                SELECT * FROM alert_events
                WHERE resolved = ?
                ORDER BY timestamp DESC
                """,
                (1 if resolved else 0,)
            )
        else:
            # Return all alerts
            cursor.execute(
                """
                SELECT * FROM alert_events
                ORDER BY timestamp DESC
                """
            )
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def get_readings_since(self, cutoff_time: str) -> List[Dict[str, Any]]:
        """
        Query temperature readings after a specific time.
        
        Retrieves all temperature readings with timestamps greater than or equal
        to the cutoff_time. Used for status checks to determine if sensors are
        actively publishing data (e.g., checking for readings within last 30 seconds).
        
        Args:
            cutoff_time: ISO 8601 formatted timestamp - only readings at or after
                        this time are returned
                        
        Returns:
            List of dictionaries containing temperature reading records
        """
        cursor = self.connection.cursor()
        
        # Use idx_timestamp index for efficient time-based query
        cursor.execute(
            """
            SELECT * FROM temperature_readings
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            """,
            (cutoff_time,)
        )
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    
    def close(self) -> None:
        """
        Close the database connection.
        
        Should be called during application shutdown to ensure proper cleanup.
        """
        if self.connection:
            self.connection.close()
            print("Database connection closed")
