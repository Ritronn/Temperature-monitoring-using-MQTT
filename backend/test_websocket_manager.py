"""
Unit tests for WebSocket manager.

Tests cover:
- Connection lifecycle (connect/disconnect)
- Broadcasting temperature readings
- Broadcasting alert events
- Error handling and automatic cleanup of failed connections
- Message format validation
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from websocket_manager import WebSocketManager
from models import TemperatureReading, AlertEvent


@pytest.fixture
def ws_manager():
    """Create a WebSocketManager instance for testing."""
    return WebSocketManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.send_text = AsyncMock()
    return ws


@pytest.fixture
def sample_reading():
    """Create a sample temperature reading."""
    return TemperatureReading(
        device_id="sensor-001",
        temperature=25.5,
        unit="C",
        timestamp="2024-01-15T10:30:45Z"
    )


@pytest.fixture
def sample_alert():
    """Create a sample alert event."""
    return AlertEvent(
        device_id="sensor-001",
        temperature=37.5,
        threshold=35.0,
        alert_type="high_temperature",
        timestamp="2024-01-15T10:35:12Z",
        resolved=False
    )


class TestWebSocketManager:
    """Test suite for WebSocketManager class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, ws_manager):
        """Test that WebSocketManager initializes with empty connections."""
        assert len(ws_manager.active_connections) == 0
        assert ws_manager.loop is None
    
    @pytest.mark.asyncio
    async def test_connect_single_client(self, ws_manager, mock_websocket):
        """Test connecting a single WebSocket client."""
        await ws_manager.connect(mock_websocket)
        
        # Verify websocket.accept() was called
        mock_websocket.accept.assert_called_once()
        
        # Verify connection was added to active connections
        assert len(ws_manager.active_connections) == 1
        assert mock_websocket in ws_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_connect_multiple_clients(self, ws_manager):
        """Test connecting multiple WebSocket clients."""
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws3 = MagicMock()
        ws3.accept = AsyncMock()
        
        await ws_manager.connect(ws1)
        await ws_manager.connect(ws2)
        await ws_manager.connect(ws3)
        
        assert len(ws_manager.active_connections) == 3
        assert ws1 in ws_manager.active_connections
        assert ws2 in ws_manager.active_connections
        assert ws3 in ws_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_disconnect_client(self, ws_manager, mock_websocket):
        """Test disconnecting a WebSocket client."""
        await ws_manager.connect(mock_websocket)
        assert len(ws_manager.active_connections) == 1
        
        ws_manager.disconnect(mock_websocket)
        
        assert len(ws_manager.active_connections) == 0
        assert mock_websocket not in ws_manager.active_connections
    
    @pytest.mark.asyncio
    async def test_disconnect_nonexistent_client(self, ws_manager, mock_websocket):
        """Test that disconnecting a non-connected client doesn't raise error."""
        # Should not raise any exception
        ws_manager.disconnect(mock_websocket)
        assert len(ws_manager.active_connections) == 0
    
    @pytest.mark.asyncio
    async def test_broadcast_reading_format(self, ws_manager, mock_websocket, sample_reading):
        """Test that temperature readings are broadcast with correct format."""
        await ws_manager.connect(mock_websocket)
        await ws_manager.broadcast_reading(sample_reading)
        
        # Verify send_text was called
        mock_websocket.send_text.assert_called_once()
        
        # Verify message format
        sent_message = mock_websocket.send_text.call_args[0][0]
        message_dict = json.loads(sent_message)
        
        assert message_dict["type"] == "temperature"
        assert "data" in message_dict
        assert message_dict["data"]["device_id"] == "sensor-001"
        assert message_dict["data"]["temperature"] == 25.5
        assert message_dict["data"]["unit"] == "C"
        assert message_dict["data"]["timestamp"] == "2024-01-15T10:30:45Z"
    
    @pytest.mark.asyncio
    async def test_broadcast_alert_format(self, ws_manager, mock_websocket, sample_alert):
        """Test that alert events are broadcast with correct format."""
        await ws_manager.connect(mock_websocket)
        await ws_manager.broadcast_alert(sample_alert)
        
        # Verify send_text was called
        mock_websocket.send_text.assert_called_once()
        
        # Verify message format
        sent_message = mock_websocket.send_text.call_args[0][0]
        message_dict = json.loads(sent_message)
        
        assert message_dict["type"] == "alert"
        assert "data" in message_dict
        assert message_dict["data"]["device_id"] == "sensor-001"
        assert message_dict["data"]["temperature"] == 37.5
        assert message_dict["data"]["threshold"] == 35.0
        assert message_dict["data"]["alert_type"] == "high_temperature"
        assert message_dict["data"]["resolved"] is False
    
    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(self, ws_manager, sample_reading):
        """Test broadcasting to multiple connected clients."""
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_text = AsyncMock()
        
        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock()
        
        ws3 = MagicMock()
        ws3.accept = AsyncMock()
        ws3.send_text = AsyncMock()
        
        await ws_manager.connect(ws1)
        await ws_manager.connect(ws2)
        await ws_manager.connect(ws3)
        
        await ws_manager.broadcast_reading(sample_reading)
        
        # Verify all clients received the message
        ws1.send_text.assert_called_once()
        ws2.send_text.assert_called_once()
        ws3.send_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcast_no_connections(self, ws_manager, sample_reading):
        """Test broadcasting when no connections are active."""
        # Should not raise any exception
        await ws_manager.broadcast_reading(sample_reading)
        assert len(ws_manager.active_connections) == 0
    
    @pytest.mark.asyncio
    async def test_error_handling_cleanup(self, ws_manager, sample_reading):
        """Test that failed connections are automatically cleaned up."""
        # Create mock websockets - one working, one failing
        ws_working = MagicMock()
        ws_working.accept = AsyncMock()
        ws_working.send_text = AsyncMock()
        
        ws_failing = MagicMock()
        ws_failing.accept = AsyncMock()
        ws_failing.send_text = AsyncMock(side_effect=Exception("Connection closed"))
        
        await ws_manager.connect(ws_working)
        await ws_manager.connect(ws_failing)
        
        assert len(ws_manager.active_connections) == 2
        
        # Broadcast should remove the failing connection
        await ws_manager.broadcast_reading(sample_reading)
        
        # Verify working connection still active, failing connection removed
        assert len(ws_manager.active_connections) == 1
        assert ws_working in ws_manager.active_connections
        assert ws_failing not in ws_manager.active_connections
        
        # Verify working connection still receives messages
        ws_working.send_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcast_all_connections_fail(self, ws_manager, sample_reading):
        """Test broadcasting when all connections fail."""
        ws1 = MagicMock()
        ws1.accept = AsyncMock()
        ws1.send_text = AsyncMock(side_effect=Exception("Connection 1 failed"))
        
        ws2 = MagicMock()
        ws2.accept = AsyncMock()
        ws2.send_text = AsyncMock(side_effect=Exception("Connection 2 failed"))
        
        await ws_manager.connect(ws1)
        await ws_manager.connect(ws2)
        
        assert len(ws_manager.active_connections) == 2
        
        # Broadcast should remove all failing connections
        await ws_manager.broadcast_reading(sample_reading)
        
        # All connections should be removed
        assert len(ws_manager.active_connections) == 0
    
    @pytest.mark.asyncio
    async def test_connection_limit(self, ws_manager):
        """Test that manager can handle up to 10 concurrent connections (requirement 5.6)."""
        connections = []
        
        for i in range(10):
            ws = MagicMock()
            ws.accept = AsyncMock()
            ws.send_text = AsyncMock()
            connections.append(ws)
            await ws_manager.connect(ws)
        
        assert len(ws_manager.active_connections) == 10
        
        # Broadcast to all connections
        sample_reading = TemperatureReading(
            device_id="sensor-001",
            temperature=25.5,
            unit="C",
            timestamp="2024-01-15T10:30:45Z"
        )
        
        await ws_manager.broadcast_reading(sample_reading)
        
        # Verify all connections received the message
        for ws in connections:
            ws.send_text.assert_called_once()
