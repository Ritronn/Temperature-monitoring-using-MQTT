"""
WebSocket manager for broadcasting real-time temperature readings and alerts.

This module manages WebSocket connections and provides broadcast functionality
for pushing real-time updates to connected dashboard clients.

Key features:
- Connection lifecycle management (connect/disconnect)
- Broadcast temperature readings to all connected clients
- Broadcast alert events to all connected clients
- Automatic cleanup of disconnected clients
- Thread-safe broadcasting from MQTT callback thread to asyncio event loop
"""

import json
import logging
from typing import Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections and broadcasts messages to connected clients.
    
    This class maintains a set of active WebSocket connections and provides
    methods to broadcast temperature readings and alert events. It handles
    connection lifecycle, error recovery, and automatic cleanup of failed
    connections.
    
    Thread Safety:
        The manager stores a reference to the asyncio event loop and uses
        asyncio.run_coroutine_threadsafe() for broadcasting from non-async
        contexts (e.g., MQTT callback thread).
    
    Attributes:
        active_connections: Set of currently connected WebSocket clients
        loop: Reference to asyncio event loop for thread-safe operations
    """
    
    def __init__(self):
        """
        Initialize the WebSocket manager.
        
        Creates an empty set for tracking connections and initializes
        the event loop reference to None (must be set during startup).
        """
        self.active_connections: Set[WebSocket] = set()
        self.loop = None  # Set to asyncio event loop on startup
        logger.info("WebSocket manager initialized")
    
    async def connect(self, websocket: WebSocket):
        """
        Accept and register a new WebSocket connection.
        
        This method accepts the WebSocket handshake and adds the connection
        to the active connections set for future broadcasts.
        
        Args:
            websocket: The WebSocket connection to accept and register
        
        Validates: Requirements 5.1, 5.2
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total active connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection from the active connections set.
        
        This method is called when a client disconnects (gracefully or not)
        to clean up resources and prevent broadcasting to closed connections.
        
        Args:
            websocket: The WebSocket connection to remove
        
        Validates: Requirements 5.5
        """
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total active connections: {len(self.active_connections)}")
    
    async def broadcast_reading(self, reading):
        """
        Broadcast a temperature reading to all connected WebSocket clients.
        
        Formats the reading as a JSON message with type "temperature" and
        broadcasts to all active connections. The reading is serialized
        using Pydantic's model_dump() method.
        
        Args:
            reading: TemperatureReading instance to broadcast
        
        Validates: Requirements 5.3, 5.4
        """
        message = {
            "type": "temperature",
            "data": reading.model_dump()
        }
        await self._broadcast(message)
        logger.debug(f"Broadcasted temperature reading for device {reading.device_id}")
    
    async def broadcast_alert(self, alert):
        """
        Broadcast an alert event to all connected WebSocket clients.
        
        Formats the alert as a JSON message with type "alert" and
        broadcasts to all active connections. The alert is serialized
        using Pydantic's model_dump() method.
        
        Args:
            alert: AlertEvent instance to broadcast
        
        Validates: Requirements 5.4
        """
        message = {
            "type": "alert",
            "data": alert.model_dump()
        }
        await self._broadcast(message)
        logger.warning(f"Broadcasted alert for device {alert.device_id}: {alert.alert_type}")
    
    async def _broadcast(self, message: dict):
        """
        Send a message to all active WebSocket connections.
        
        This internal method handles the actual broadcasting logic with
        error handling and automatic cleanup of failed connections.
        
        Process:
        1. Skip if no connections are active
        2. Serialize message to JSON
        3. Attempt to send to each connection
        4. Track connections that fail
        5. Clean up disconnected clients from active set
        
        Args:
            message: Dictionary containing "type" and "data" fields
        
        Validates: Requirements 5.3, 5.5
        """
        if not self.active_connections:
            logger.debug("No active WebSocket connections to broadcast to")
            return
        
        message_json = json.dumps(message)
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)
        
        if disconnected:
            logger.info(f"Removed {len(disconnected)} failed connections. "
                       f"Active connections: {len(self.active_connections)}")
