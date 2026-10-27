"""
Integration test for DatabaseManager query operations.

Tests realistic scenarios combining multiple query methods to verify
they work correctly together.
"""

import unittest
from datetime import datetime, timedelta
import tempfile
import os

from database import DatabaseManager


class TestDatabaseIntegration(unittest.TestCase):
    """Integration tests for DatabaseManager query operations."""
    
    def setUp(self):
        """Set up database for integration testing."""
        self.temp_db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        self.db = DatabaseManager(self.temp_db_path)
    
    def tearDown(self):
        """Clean up database after tests."""
        self.db.close()
        os.close(self.temp_db_fd)
        os.unlink(self.temp_db_path)
    
    def test_sensor_monitoring_workflow(self):
        """
        Test realistic sensor monitoring workflow:
        1. Sensors publish readings over time
        2. Query latest readings to show current status
        3. Temperature exceeds threshold, alert created
        4. Query unresolved alerts
        5. Temperature normalizes, alert resolved
        6. Query historical data for analysis
        """
        base_time = datetime.utcnow()
        
        # Step 1: Simulate sensor readings over time
        for i in range(10):
            reading = {
                'device_id': 'sensor-001',
                'temperature': 30.0 + i,  # Temperature rising
                'unit': 'C',
                'timestamp': (base_time - timedelta(minutes=50-i*5)).isoformat() + 'Z'
            }
            self.db.insert_reading(reading)
        
        # Step 2: Check latest reading (should show high temperature)
        latest = self.db.get_latest_readings()
        self.assertEqual(len(latest), 1)
        self.assertEqual(latest[0]['device_id'], 'sensor-001')
        self.assertEqual(latest[0]['temperature'], 39.0)  # Last reading
        
        # Step 3: Alert triggered when temperature exceeded 35°C
        alert = {
            'device_id': 'sensor-001',
            'temperature': 36.0,
            'threshold': 35.0,
            'alert_type': 'high_temperature',
            'timestamp': (base_time - timedelta(minutes=25)).isoformat() + 'Z',
            'resolved': False
        }
        self.db.insert_alert(alert)
        
        # Step 4: Check unresolved alerts
        unresolved_alerts = self.db.get_alerts(resolved=False)
        self.assertEqual(len(unresolved_alerts), 1)
        self.assertEqual(unresolved_alerts[0]['device_id'], 'sensor-001')
        self.assertFalse(unresolved_alerts[0]['resolved'])
        
        # Step 5: Temperature normalizes, add normal readings
        for i in range(5):
            reading = {
                'device_id': 'sensor-001',
                'temperature': 34.0 - i,  # Temperature falling
                'unit': 'C',
                'timestamp': (base_time - timedelta(minutes=20-i*4)).isoformat() + 'Z'
            }
            self.db.insert_reading(reading)
        
        # Resolve the alert
        self.db.resolve_alerts('sensor-001')
        
        # Verify alert is now resolved
        unresolved_alerts = self.db.get_alerts(resolved=False)
        self.assertEqual(len(unresolved_alerts), 0)
        
        resolved_alerts = self.db.get_alerts(resolved=True)
        self.assertEqual(len(resolved_alerts), 1)
        
        # Step 6: Query historical data for analysis
        start_time = (base_time - timedelta(hours=1)).isoformat() + 'Z'
        end_time = base_time.isoformat() + 'Z'
        history = self.db.get_readings_history(start_time, end_time, device_id='sensor-001')
        
        # Should have all 15 readings
        self.assertEqual(len(history), 15)
        
        # Verify readings are in ascending time order
        timestamps = [r['timestamp'] for r in history]
        self.assertEqual(timestamps, sorted(timestamps))
    
    def test_multi_device_status_check(self):
        """
        Test status checking across multiple devices:
        1. Multiple sensors publishing at different rates
        2. Check which sensors are online (have recent readings)
        3. Get latest reading per device
        """
        base_time = datetime.utcnow()
        
        # Active sensor - recent readings
        for i in range(3):
            reading = {
                'device_id': 'sensor-001',
                'temperature': 22.0 + i,
                'unit': 'C',
                'timestamp': (base_time - timedelta(seconds=30-i*10)).isoformat() + 'Z'
            }
            self.db.insert_reading(reading)
        
        # Another active sensor
        reading = {
            'device_id': 'sensor-002',
            'temperature': 28.5,
            'unit': 'C',
            'timestamp': (base_time - timedelta(seconds=15)).isoformat() + 'Z'
        }
        self.db.insert_reading(reading)
        
        # Inactive sensor - old readings only
        old_reading = {
            'device_id': 'sensor-003',
            'temperature': 25.0,
            'unit': 'C',
            'timestamp': (base_time - timedelta(minutes=5)).isoformat() + 'Z'
        }
        self.db.insert_reading(old_reading)
        
        # Check sensors online in last minute
        cutoff_time = (base_time - timedelta(seconds=60)).isoformat() + 'Z'
        recent_readings = self.db.get_readings_since(cutoff_time)
        
        # Should have readings from sensor-001 and sensor-002 (not sensor-003)
        active_devices = set(r['device_id'] for r in recent_readings)
        self.assertIn('sensor-001', active_devices)
        self.assertIn('sensor-002', active_devices)
        self.assertEqual(len(recent_readings), 4)  # 3 from sensor-001, 1 from sensor-002
        
        # Get latest reading per device
        latest = self.db.get_latest_readings()
        self.assertEqual(len(latest), 3)  # All three devices have readings
        
        # Verify we got the most recent reading for each
        device_temps = {r['device_id']: r['temperature'] for r in latest}
        self.assertEqual(device_temps['sensor-001'], 24.0)  # Last of the series
        self.assertEqual(device_temps['sensor-002'], 28.5)
        self.assertEqual(device_temps['sensor-003'], 25.0)
    
    def test_alert_duplicate_prevention(self):
        """
        Test that duplicate alerts are prevented:
        1. Create alert for high temperature
        2. Attempt to create another alert for same device
        3. Verify only one alert exists
        """
        base_time = datetime.utcnow()
        
        # Create first alert
        alert1 = {
            'device_id': 'sensor-001',
            'temperature': 36.0,
            'threshold': 35.0,
            'alert_type': 'high_temperature',
            'timestamp': (base_time - timedelta(minutes=10)).isoformat() + 'Z',
            'resolved': False
        }
        self.db.insert_alert(alert1)
        
        # Attempt to create duplicate alert
        alert2 = {
            'device_id': 'sensor-001',
            'temperature': 37.5,
            'threshold': 35.0,
            'alert_type': 'high_temperature',
            'timestamp': (base_time - timedelta(minutes=5)).isoformat() + 'Z',
            'resolved': False
        }
        self.db.insert_alert(alert2)
        
        # Should only have one unresolved alert
        unresolved = self.db.get_alerts(resolved=False)
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0]['temperature'], 36.0)  # First alert remains
        
        # After resolving, can create new alert
        self.db.resolve_alerts('sensor-001')
        
        alert3 = {
            'device_id': 'sensor-001',
            'temperature': 38.0,
            'threshold': 35.0,
            'alert_type': 'high_temperature',
            'timestamp': base_time.isoformat() + 'Z',
            'resolved': False
        }
        self.db.insert_alert(alert3)
        
        # Now should have one unresolved and one resolved
        unresolved = self.db.get_alerts(resolved=False)
        resolved = self.db.get_alerts(resolved=True)
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(len(resolved), 1)
        self.assertEqual(unresolved[0]['temperature'], 38.0)  # New alert


if __name__ == '__main__':
    unittest.main()
