"""
MQTT Client for ThermosenseIoT Dashboard

This module implements the MQTT client component that subscribes to temperature
sensor topics and processes incoming messages. The client:
- Connects to the MQTT broker with automatic reconnection
- Subscribes to sensors/temperature and sensors/status topics with QoS 1
- Validates and processes temperature readings
- Persists readings to the database
- Checks temperature thresholds and creates/resolves alerts
- Broadcasts readings and alerts to WebSocket clients via thread-safe bridging

The MQTT client runs in a separate thread using paho-mqtt's loop_start() method,
and bridges to the asyncio event loop for WebSocket broadcasting.
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Optional
import paho.mqtt.client as mqtt
from pydantic import ValidationError

from models import TemperatureReading, AlertEvent
from database import DatabaseManager
from websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)


class MQTTClient:
    """
    MQTT client for subscribing to temperature sensor messages.
    
    This class manages the MQTT connection lifecycle, message processing,
    threshold checking, and integration with database and WebSocket components.
    
    Attributes:
        config (dict): Configuration containing MQTT broker settings and threshold
        db (DatabaseManager): Database manager for persisting readings and alerts
        ws_manager (WebSocketManager): WebSocket manager for broadcasting updates
        client (mqtt.Client): Paho MQTT client instance
        threshold (float): Current temperature threshold for alerts (in Celsius)
        is_connected (bool): Current connection status
    """
    
    def __init__(self, config: dict, db_manager: DatabaseManager, ws_manager: WebSocketManager, email_notifier=None):
        """
        Initialize the MQTT client with dependencies.
        
        Args:
            config: Configuration dictionary containing mqtt_broker_host,
                   mqtt_broker_port, and default_threshold
            db_manager: DatabaseManager instance for data persistence
            ws_manager: WebSocketManager instance for real-time broadcasting
            email_notifier: Optional EmailNotifier instance for email alerts
        """
        self.config = config
        self.db = db_manager
        self.ws_manager = ws_manager
        self.email_notifier = email_notifier
        self.threshold = config.get("default_threshold", 35.0)
        self.is_connected = False
        
        # Create MQTT client instance
        self.client = mqtt.Client(client_id="thermosense_backend", protocol=mqtt.MQTTv311)
        
        # Set up callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        logger.info("MQTT client initialized")
    
    def connect(self) -> None:
        """
        Establish connection to the MQTT broker and start the network loop.
        
        This method connects to the broker and starts the background network thread
        using loop_start(). The on_connect callback will be triggered upon successful
        connection, which will subscribe to the necessary topics.
        
        Raises:
            Exception: If connection to the broker fails
        """
        try:
            broker_host = self.config["mqtt_broker_host"]
            broker_port = self.config["mqtt_broker_port"]
            
            logger.info(f"Connecting to MQTT broker at {broker_host}:{broker_port}")
            self.client.connect(broker_host, broker_port, keepalive=60)
            
            # Start the network loop in a separate thread
            self.client.loop_start()
            logger.info("MQTT client network loop started")
            
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        Callback triggered when the client connects to the MQTT broker.
        
        This callback subscribes to the necessary topics with QoS level 1
        for reliable message delivery.
        
        Args:
            client: The MQTT client instance
            userdata: User-defined data (unused)
            flags: Connection flags
            rc: Connection result code (0 = success)
        """
        if rc == 0:
            self.is_connected = True
            logger.info("Successfully connected to MQTT broker")
            
            # Subscribe to temperature readings topic with QoS 1
            client.subscribe("sensors/temperature", qos=1)
            logger.info("Subscribed to sensors/temperature with QoS 1")
            
            # Subscribe to sensor status topic with QoS 1
            client.subscribe("sensors/status", qos=1)
            logger.info("Subscribed to sensors/status with QoS 1")
        else:
            self.is_connected = False
            logger.error(f"Failed to connect to MQTT broker with result code: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """
        Callback triggered when the client disconnects from the MQTT broker.
        
        Logs the disconnection and connection state. The paho-mqtt client will
        automatically attempt reconnection when using loop_start().
        
        Args:
            client: The MQTT client instance
            userdata: User-defined data (unused)
            rc: Disconnection result code (0 = clean disconnect, >0 = unexpected)
        """
        self.is_connected = False
        if rc == 0:
            logger.info("Cleanly disconnected from MQTT broker")
        else:
            logger.warning(f"Unexpectedly disconnected from MQTT broker (rc={rc}), will attempt reconnection")
    
    def _on_message(self, client, userdata, msg):
        """
        Callback triggered when a message is received from a subscribed topic.
        
        Routes messages to appropriate handlers based on topic.
        
        Args:
            client: The MQTT client instance
            userdata: User-defined data (unused)
            msg: The MQTT message (contains topic and payload)
        """
        logger.debug(f"Received message on topic {msg.topic}: {msg.payload}")
        
        try:
            if msg.topic == "sensors/temperature":
                self._handle_temperature_reading(msg.payload)
            elif msg.topic == "sensors/status":
                self._handle_status_message(msg.payload)
            else:
                logger.warning(f"Received message on unexpected topic: {msg.topic}")
        except Exception as e:
            logger.error(f"Error processing message from topic {msg.topic}: {e}")
    
    def _handle_temperature_reading(self, payload: bytes) -> None:
        """
        Process a temperature reading message.
        
        This method:
        1. Parses and validates the JSON payload
        2. Persists the reading to the database
        3. Checks the temperature against the threshold
        4. Creates or resolves alerts as needed
        5. Broadcasts the reading to WebSocket clients
        
        Args:
            payload: Raw MQTT message payload (JSON bytes)
        """
        try:
            # Parse JSON payload
            data = json.loads(payload.decode('utf-8'))
            
            # Validate using Pydantic model
            reading = TemperatureReading(**data)
            
            # Persist to database
            self.db.insert_reading(reading)
            logger.debug(f"Persisted temperature reading: {reading.device_id} = {reading.temperature}°{reading.unit}")
            
            # Check threshold and handle alerts
            self._check_threshold(reading)
            
            # Broadcast to WebSocket clients
            self._broadcast_reading(reading)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in temperature message: {e}")
        except ValidationError as e:
            logger.error(f"Invalid temperature reading format: {e}")
        except Exception as e:
            logger.error(f"Error handling temperature reading: {e}")
    
    def _handle_status_message(self, payload: bytes) -> None:
        """
        Process a sensor status message.
        
        Logs the sensor status for monitoring purposes.
        
        Args:
            payload: Raw MQTT message payload (JSON bytes)
        """
        try:
            data = json.loads(payload.decode('utf-8'))
            device_id = data.get("device_id", "unknown")
            status = data.get("status", "unknown")
            logger.info(f"Sensor status update: {device_id} is {status}")
        except Exception as e:
            logger.error(f"Error handling status message: {e}")
    
    def _check_threshold(self, reading: TemperatureReading) -> None:
        """
        Check if the temperature reading exceeds the threshold and manage alerts.
        
        If temperature exceeds threshold:
        - Creates a new alert event (if no unresolved alert exists for this device)
        - Persists the alert to the database
        - Broadcasts the alert to WebSocket clients
        
        If temperature is at or below threshold:
        - Resolves any existing unresolved alerts for this device
        
        Args:
            reading: Validated temperature reading to check
        """
        # Convert temperature to Celsius for threshold comparison
        # (Currently assumes all readings are in Celsius)
        temp_celsius = reading.temperature
        
        if temp_celsius > self.threshold:
            # Temperature exceeds threshold - create alert
            # Check if there's already an unresolved alert for this device
            existing_alerts = self.db.get_alerts(resolved=False)
            device_has_alert = any(
                alert["device_id"] == reading.device_id 
                for alert in existing_alerts
            )
            
            if not device_has_alert:
                # Create new alert event
                alert = AlertEvent(
                    device_id=reading.device_id,
                    temperature=reading.temperature,
                    threshold=self.threshold,
                    alert_type="high_temperature",
                    timestamp=reading.timestamp,
                    resolved=False
                )
                
                self.db.insert_alert(alert)
                logger.warning(f"Alert created: {reading.device_id} temperature {temp_celsius}°C exceeds threshold {self.threshold}°C")
                
                # Broadcast alert to WebSocket clients
                self._broadcast_alert(alert)

                # Send email notification via SMTP
                if self.email_notifier:
                    try:
                        self.email_notifier.send_alert_email(alert)
                    except Exception as e:
                        logger.error(f"Error triggering alert email: {e}")
        else:
            # Temperature is at or below threshold - resolve any existing alerts
            self.db.resolve_alerts(reading.device_id)
            logger.debug(f"Checked/resolved alerts for device {reading.device_id}")
    
    def _broadcast_reading(self, reading: TemperatureReading) -> None:
        """
        Broadcast a temperature reading to all connected WebSocket clients.
        
        Uses asyncio.run_coroutine_threadsafe to bridge from the MQTT thread
        to the asyncio event loop where the WebSocket manager operates.
        
        Args:
            reading: Temperature reading to broadcast
        """
        try:
            if self.ws_manager and self.ws_manager.loop and self.ws_manager.loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.ws_manager.broadcast_reading(reading),
                    self.ws_manager.loop
                )
            elif self.ws_manager:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self.ws_manager.broadcast_reading(reading))
                except RuntimeError:
                    pass
        except Exception as e:
            logger.error(f"Error broadcasting temperature reading: {e}")
    
    def _broadcast_alert(self, alert: AlertEvent) -> None:
        """
        Broadcast an alert event to all connected WebSocket clients.
        
        Uses asyncio.run_coroutine_threadsafe to bridge from the MQTT thread
        to the asyncio event loop where the WebSocket manager operates.
        
        Args:
            alert: Alert event to broadcast
        """
        try:
            if self.ws_manager and self.ws_manager.loop and self.ws_manager.loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.ws_manager.broadcast_alert(alert),
                    self.ws_manager.loop
                )
            elif self.ws_manager:
                try:
                    loop = asyncio.get_running_loop()
                    loop.create_task(self.ws_manager.broadcast_alert(alert))
                except RuntimeError:
                    pass
        except Exception as e:
            logger.error(f"Error broadcasting alert: {e}")
    
    def disconnect(self) -> None:
        """
        Gracefully disconnect from the MQTT broker.
        
        This method stops the network loop and closes the connection cleanly.
        Should be called during application shutdown to ensure proper cleanup.
        """
        logger.info("Disconnecting from MQTT broker")
        try:
            # Stop the network loop thread
            self.client.loop_stop()
            logger.debug("MQTT network loop stopped")
            
            # Disconnect from the broker
            self.client.disconnect()
            self.is_connected = False
            logger.info("Successfully disconnected from MQTT broker")
        except Exception as e:
            logger.error(f"Error during MQTT disconnect: {e}")
    
    def update_threshold(self, new_threshold: float) -> None:
        """
        Update the temperature threshold for alert generation.
        
        Args:
            new_threshold: New threshold value in Celsius
        """
        self.threshold = new_threshold
        logger.info(f"Temperature threshold updated to {new_threshold}°C")
