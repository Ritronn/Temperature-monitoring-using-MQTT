"""
Unit tests for DatabaseManager query operations.

Tests the database query methods: get_readings_history, get_latest_readings,
get_alerts, and get_readings_since.
"""

import unittest
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from database import DatabaseManager


class TestDatabaseQueryOperations(unittest.TestCase):
    """Test suite for DatabaseManager query methods."""
    
    def setUp(self):
        """Set up in-memory database for each test."""
        # Create temporary database file
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        self.db = DatabaseManager(self.temp_db_path)
        
        # Insert sample temperature readings for testing
        self._insert_sample_readings()
        
        # Insert sample alerts for testing
        self._insert_sample_alerts()
    
    def tearDown(self):
        """Clean up database after each test."""
        self.db.close()
        os.close(self.temp_db_fd)
        os.unlink(self.temp_db_path)
    
    def _insert_sample_readings(self):
        """Insert sample temperature readings for testing."""
        base_time = datetime.utcnow()
        
        # Insert readings for device-001 over past hour
        for i in range(5):
            reading = {
                'device_id': 'sensor-001',
                'temperature': 20.0 + i,
                'unit': 'C',
                'timestamp': (base_time - timedelta(minutes=60-i*10)).isoformat() + 'Z'
            }
            self.db.insert_reading(reading)
        
        # Insert readings for device-002 over past hour
        for i in range(3):
            reading = {
                'device_id': 'sensor-002',
                'temperature': 25.0 + i,
                'unit': 'C',
                'timestamp': (base_time - timedelta(minutes=50-i*15)).isoformat() + 'Z'
            }
            self.db.insert_reading(reading)
        
        # Insert old readings (more than 1 day old) for cleanup testing
        old_time = base_time - timedelta(days=8)
        old_reading = {
            'device_id': 'sensor-001',
            'temperature': 15.0,
            'unit': 'C',
            'timestamp': old_time.isoformat() + 'Z'
        }
        self.db.insert_reading(old_reading)
    
    def _insert_sample_alerts(self):
        """Insert sample alerts for testing."""
        base_time = datetime.utcnow()
        
        # Insert unresolved alert for sensor-001
        alert = {
            'device_id': 'sensor-001',
            'temperature': 36.5,
            'threshold': 35.0,
            'alert_type': 'high_temperature',
            'timestamp': (base_time - timedelta(minutes=30)).isoformat() + 'Z',
            'resolved': False
        }
        self.db.insert_alert(alert)
        
        # Insert resolved alert for sensor-002
        alert = {
            'device_id': 'sensor-002',
            'temperature': 37.0,
            'threshold': 35.0,
            'alert_type': 'high_temperature',
            'timestamp': (base_time - timedelta(hours=2)).isoformat() + 'Z',
            'resolved': True
        }
        self.db.insert_alert(alert)
        
        # Resolve it explicitly
        self.db.resolve_alerts('sensor-002')
    
    def test_get_readings_history_all_devices(self):
        """Test retrieving historical readings for all devices within time range."""
        base_time = datetime.utcnow()
        start_time = (base_time - timedelta(hours=2)).isoformat() + 'Z'
        end_time = base_time.isoformat() + 'Z'
        
        readings = self.db.get_readings_history(start_time, end_time)
        
        # Should get readings from both devices (excluding old readings)
        self.assertGreater(len(readings), 0)
        self.assertLessEqual(len(readings), 8)  # 5 from sensor-001 + 3 from sensor-002
        
        # Verify structure of returned readings
        for reading in readings:
            self.assertIn('device_id', reading)
            self.assertIn('temperature', reading)
            self.assertIn('unit', reading)
            self.assertIn('timestamp', reading)
        
        # Verify readings are ordered by timestamp ascending
        timestamps = [reading['timestamp'] for reading in readings]
        self.assertEqual(timestamps, sorted(timestamps))
    
    def test_get_readings_history_single_device(self):
        """Test retrieving historical readings filtered by device_id."""
        base_time = datetime.utcnow()
        start_time = (base_time - timedelta(hours=2)).isoformat() + 'Z'
        end_time = base_time.isoformat() + 'Z'
        
        readings = self.db.get_readings_history(start_time, end_time, device_id='sensor-001')
        
        # Should only get readings from sensor-001
        self.assertGreater(len(readings), 0)
        for reading in readings:
            self.assertEqual(reading['device_id'], 'sensor-001')
    
    def test_get_readings_history_empty_range(self):
        """Test that querying future time range returns empty list."""
        future_start = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'
        future_end = (datetime.utcnow() + timedelta(days=2)).isoformat() + 'Z'
        
        readings = self.db.get_readings_history(future_start, future_end)
        
        self.assertEqual(len(readings), 0)
    
    def test_get_latest_readings(self):
        """Test retrieving most recent reading per device."""
        readings = self.db.get_latest_readings()
        
        # Should get one reading per device
        device_ids = [reading['device_id'] for reading in readings]
        self.assertEqual(len(device_ids), len(set(device_ids)))  # All unique
        
        # Should have readings for both sensors
        self.assertIn('sensor-001', device_ids)
        self.assertIn('sensor-002', device_ids)
        
        # Verify each reading has required fields
        for reading in readings:
            self.assertIn('device_id', reading)
            self.assertIn('temperature', reading)
            self.assertIn('unit', reading)
            self.assertIn('timestamp', reading)
    
    def test_get_latest_readings_empty_database(self):
        """Test get_latest_readings returns empty list when no readings exist."""
        # Create fresh database with no data
        temp_fd, temp_path = tempfile.mkstemp(suffix='.db')
        temp_db = DatabaseManager(temp_path)
        
        readings = temp_db.get_latest_readings()
        
        self.assertEqual(len(readings), 0)
        
        # Cleanup
        temp_db.close()
        os.close(temp_fd)
        os.unlink(temp_path)
    
    def test_get_alerts_all(self):
        """Test retrieving all alerts without filter."""
        alerts = self.db.get_alerts()
        
        # Should get both resolved and unresolved alerts
        self.assertGreater(len(alerts), 0)
        
        # Verify structure
        for alert in alerts:
            self.assertIn('device_id', alert)
            self.assertIn('temperature', alert)
            self.assertIn('threshold', alert)
            self.assertIn('alert_type', alert)
            self.assertIn('timestamp', alert)
            self.assertIn('resolved', alert)
        
        # Verify ordered by timestamp descending (most recent first)
        timestamps = [alert['timestamp'] for alert in alerts]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))
    
    def test_get_alerts_unresolved_only(self):
        """Test retrieving only unresolved alerts."""
        alerts = self.db.get_alerts(resolved=False)
        
        # Should only get unresolved alerts
        self.assertGreater(len(alerts), 0)
        for alert in alerts:
            self.assertEqual(alert['resolved'], 0)  # SQLite stores False as 0
    
    def test_get_alerts_resolved_only(self):
        """Test retrieving only resolved alerts."""
        alerts = self.db.get_alerts(resolved=True)
        
        # Should only get resolved alerts
        self.assertGreater(len(alerts), 0)
        for alert in alerts:
            self.assertEqual(alert['resolved'], 1)  # SQLite stores True as 1
    
    def test_get_alerts_empty(self):
        """Test get_alerts returns empty list when no alerts exist."""
        # Create fresh database with no alerts
        temp_fd, temp_path = tempfile.mkstemp(suffix='.db')
        temp_db = DatabaseManager(temp_path)
        
        alerts = temp_db.get_alerts()
        
        self.assertEqual(len(alerts), 0)
        
        # Cleanup
        temp_db.close()
        os.close(temp_fd)
        os.unlink(temp_path)
    
    def test_get_readings_since(self):
        """Test retrieving readings after a cutoff time."""
        # Query for readings in last 45 minutes
        cutoff_time = (datetime.utcnow() - timedelta(minutes=45)).isoformat() + 'Z'
        
        readings = self.db.get_readings_since(cutoff_time)
        
        # Should get recent readings
        self.assertGreater(len(readings), 0)
        
        # Verify all readings are after cutoff
        for reading in readings:
            self.assertGreaterEqual(reading['timestamp'], cutoff_time)
        
        # Verify ordered by timestamp descending (most recent first)
        timestamps = [reading['timestamp'] for reading in readings]
        self.assertEqual(timestamps, sorted(timestamps, reverse=True))
    
    def test_get_readings_since_excludes_old_readings(self):
        """Test that get_readings_since correctly excludes old readings."""
        # Query for very recent readings (last 5 minutes)
        cutoff_time = (datetime.utcnow() - timedelta(minutes=5)).isoformat() + 'Z'
        
        readings = self.db.get_readings_since(cutoff_time)
        
        # Should get fewer readings than total
        all_readings = self.db.get_readings_history(
            (datetime.utcnow() - timedelta(days=1)).isoformat() + 'Z',
            datetime.utcnow().isoformat() + 'Z'
        )
        
        # Recent readings should be subset of all readings
        self.assertLessEqual(len(readings), len(all_readings))
    
    def test_get_readings_since_future_cutoff(self):
        """Test that future cutoff time returns empty list."""
        future_cutoff = (datetime.utcnow() + timedelta(hours=1)).isoformat() + 'Z'
        
        readings = self.db.get_readings_since(future_cutoff)
        
        self.assertEqual(len(readings), 0)


if __name__ == '__main__':
    unittest.main()
