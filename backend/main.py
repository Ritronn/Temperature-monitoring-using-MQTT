"""
ThermosenseIoT Backend Service - Main FastAPI Application

This module is the entry point for the FastAPI backend service that provides:
- HTTP REST API endpoints for data querying and system control
- WebSocket endpoint for real-time temperature broadcasting
- MQTT client integration for receiving sensor data
- SQLite database persistence for readings and alerts
- Sensor simulator process management
- Graceful startup and shutdown handling
"""

import asyncio
import logging
import os
import subprocess
import sys
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

# Import local modules - resolve path for config.json relative to project root
from config import load_config, save_config_to_file
from database import DatabaseManager
from email_notifier import EmailNotifier
from logging_config import setup_logging
from models import ConfigUpdate, TemperatureReading
from mqtt_client import MQTTClient
from websocket_manager import WebSocketManager

# ---------------------------------------------------------------------------
# Logging setup (early, before anything else)
# ---------------------------------------------------------------------------
setup_logging()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level singletons (populated in lifespan startup)
# ---------------------------------------------------------------------------
db: Optional[DatabaseManager] = None
ws_manager: Optional[WebSocketManager] = None
mqtt_client: Optional[MQTTClient] = None
email_notifier: Optional[EmailNotifier] = None
start_time: float = 0.0
simulator_process: Optional[subprocess.Popen] = None
simulator_log_file = None
app_config: dict = {}


# ---------------------------------------------------------------------------
# Cleanup background task
# ---------------------------------------------------------------------------
async def cleanup_task(database: DatabaseManager) -> None:
    """Run daily cleanup of temperature readings older than 7 days."""
    while True:
        await asyncio.sleep(86400)  # 24 hours
        try:
            database.cleanup_old_readings(days=7)
            logger.info("Daily data cleanup completed")
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}", exc_info=True)


# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(application: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    global db, ws_manager, mqtt_client, start_time, app_config

    # ---- STARTUP ----
    logger.info("Starting ThermosenseIoT backend service...")
    start_time = time.time()

    # Determine config path - look in parent directory (project root)
    config_path = Path(__file__).parent.parent / "config.json"
    if not config_path.exists():
        config_path = Path("config.json")

    try:
        app_config = load_config(str(config_path))
        logger.info(f"Configuration loaded from {config_path}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        app_config = {
            "mqtt_broker_host": "localhost",
            "mqtt_broker_port": 1883,
            "default_threshold": 35.0,
            "database_path": "thermosense.db",
            "websocket_port": 8000,
        }

    # Resolve database path relative to project root
    db_path = app_config.get("database_path", "thermosense.db")
    if not Path(db_path).is_absolute():
        db_path = str(Path(__file__).parent.parent / db_path)

    # Initialize database
    db = DatabaseManager(db_path)
    logger.info(f"Database initialized at {db_path}")

    # Initialize WebSocket manager
    ws_manager = WebSocketManager()
    ws_manager.loop = asyncio.get_event_loop()
    logger.info("WebSocket manager initialized")

    # Initialize Email Notifier
    smtp_cfg = app_config.get("smtp", {})
    email_notifier = EmailNotifier(smtp_cfg)
    logger.info("Email notifier initialized")

    # Initialize and connect MQTT client with email notifier
    mqtt_client = MQTTClient(app_config, db, ws_manager, email_notifier=email_notifier)
    try:
        mqtt_client.connect()
        logger.info("MQTT client connected")
    except Exception as e:
        logger.error(f"MQTT client failed to connect (will retry): {e}")

    # Start background cleanup task
    asyncio.create_task(cleanup_task(db))
    logger.info("Background cleanup task started")
    logger.info("ThermosenseIoT backend service started successfully")

    yield  # Application runs here

    # ---- SHUTDOWN ----
    logger.info("Shutting down ThermosenseIoT backend service...")

    # Close all WebSocket connections
    if ws_manager:
        for ws in list(ws_manager.active_connections):
            try:
                await ws.close()
            except Exception:
                pass
        logger.info("All WebSocket connections closed")

    # Disconnect MQTT client
    if mqtt_client:
        try:
            mqtt_client.disconnect()
            logger.info("MQTT client disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting MQTT: {e}")

    # Shutdown email notifier
    if email_notifier:
        try:
            email_notifier.shutdown()
            logger.info("Email notifier shutdown completed")
        except Exception as e:
            logger.error(f"Error shutting down email notifier: {e}")

    # Close database
    if db:
        try:
            db.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")

    # Stop simulator if running
    global simulator_process, simulator_log_file
    if simulator_process and simulator_process.poll() is None:
        try:
            simulator_process.terminate()
            simulator_process.wait(timeout=5)
            logger.info("Simulator process terminated")
        except Exception as e:
            logger.error(f"Error terminating simulator: {e}")

    if simulator_log_file:
        try:
            simulator_log_file.close()
            simulator_log_file = None
        except Exception:
            pass

    logger.info("ThermosenseIoT backend service stopped")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ThermosenseIoT Backend",
    description="Real-time temperature monitoring backend with MQTT, WebSocket, and REST API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _get_spike_signal_path() -> Path:
    """Return platform-appropriate path for spike signal file."""
    temp_dir = os.environ.get("TEMP", os.environ.get("TMP", "/tmp"))
    return Path(temp_dir) / "thermosense_spike_signal.txt"


# ---------------------------------------------------------------------------
# Health & Status endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["health"])
async def health_check():
    """Return service health status."""
    return {"status": "healthy"}


@app.get("/api/status", tags=["status"])
async def get_status():
    """
    Return system component status.

    Returns MQTT connection status, sensor online status (reading received in
    the last 30 seconds), and backend uptime in seconds.
    """
    uptime = int(time.time() - start_time)

    # Sensor is online if a reading was received within the last 30 seconds
    cutoff = (datetime.utcnow() - timedelta(seconds=30)).isoformat() + "Z"
    sensor_online = False
    simulator_running = simulator_process is not None and simulator_process.poll() is None

    try:
        recent = db.get_readings_since(cutoff)
        sensor_online = len(recent) > 0
    except Exception as e:
        logger.error(f"Error checking sensor status: {e}")

    return {
        "mqtt_connected": mqtt_client.is_connected if mqtt_client else False,
        "sensor_online": sensor_online,
        "backend_uptime_seconds": uptime,
        "simulator_running": simulator_running,
    }


# ---------------------------------------------------------------------------
# Readings endpoints
# ---------------------------------------------------------------------------

@app.get("/api/readings/latest", tags=["readings"])
async def get_latest_readings():
    """Return the most recent temperature reading for each device."""
    try:
        readings = db.get_latest_readings()
        return {"readings": readings}
    except Exception as e:
        logger.error(f"Database error getting latest readings: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Database unavailable")


@app.get("/api/readings/history", tags=["readings"])
async def get_readings_history(
    start_time: str,
    end_time: str,
    device_id: Optional[str] = None,
):
    """
    Return temperature readings within a time range.

    Args:
        start_time: ISO 8601 start timestamp
        end_time: ISO 8601 end timestamp
        device_id: Optional device ID filter
    """
    # Validate timestamps
    try:
        datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        datetime.fromisoformat(end_time.replace("Z", "+00:00"))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid timestamp format. Use ISO 8601 (e.g., 2024-01-15T10:30:00Z)",
        )

    try:
        readings = db.get_readings_history(start_time, end_time, device_id)
        return {"readings": readings}
    except Exception as e:
        logger.error(f"Database error getting history: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Database unavailable")


# ---------------------------------------------------------------------------
# Alerts endpoint
# ---------------------------------------------------------------------------

@app.get("/api/alerts", tags=["alerts"])
async def get_alerts(resolved: Optional[bool] = None):
    """
    Return alert events.

    Args:
        resolved: Optional filter - True for resolved alerts, False for active alerts
    """
    try:
        alerts = db.get_alerts(resolved)
        return {"alerts": alerts}
    except Exception as e:
        logger.error(f"Database error getting alerts: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Database unavailable")


# ---------------------------------------------------------------------------
# Configuration endpoints
# ---------------------------------------------------------------------------

@app.get("/api/config", tags=["config"])
async def get_config():
    """Return current threshold configuration."""
    threshold = mqtt_client.threshold if mqtt_client else app_config.get("default_threshold", 35.0)
    return {"threshold": threshold}


@app.put("/api/config", tags=["config"])
async def update_config(config_update: ConfigUpdate):
    """
    Update temperature threshold configuration.

    The threshold must be between 0 and 100 degrees Celsius.
    """
    if config_update.threshold < 0 or config_update.threshold > 100:
        raise HTTPException(
            status_code=400,
            detail="Threshold must be between 0 and 100",
        )

    # Update in-memory threshold
    if mqtt_client:
        mqtt_client.update_threshold(config_update.threshold)

    # Persist to config file
    try:
        config_path = Path(__file__).parent.parent / "config.json"
        if not config_path.exists():
            config_path = Path("config.json")
        current_config = load_config(str(config_path))
        current_config["default_threshold"] = config_update.threshold
        save_config_to_file(current_config, str(config_path))
        logger.info(f"Threshold updated to {config_update.threshold}°C and persisted")
    except Exception as e:
        logger.error(f"Error persisting threshold change: {e}")
        # Return success anyway since in-memory was updated

    return {"threshold": config_update.threshold}


# ---------------------------------------------------------------------------
# Simulator control endpoints
# ---------------------------------------------------------------------------

@app.post("/api/simulator/start", tags=["simulator"])
async def start_simulator():
    """Start the temperature sensor simulator process."""
    global simulator_process, simulator_log_file

    if simulator_process and simulator_process.poll() is None:
        raise HTTPException(status_code=400, detail="Simulator already running")

    # Resolve simulator script path
    simulator_script = Path(__file__).parent.parent / "sensor" / "simulator.py"
    config_path = Path(__file__).parent.parent / "config.json"

    if not simulator_script.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Simulator script not found at {simulator_script}",
        )

    try:
        # Redirect stdout and stderr to a log file instead of PIPE
        # to prevent OS pipe buffer exhaustion deadlock on long runs
        log_dir = Path(__file__).parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        sim_log_path = log_dir / "simulator.log"
        simulator_log_file = open(sim_log_path, "a", encoding="utf-8")

        simulator_process = subprocess.Popen(
            [sys.executable, str(simulator_script), "--config", str(config_path)],
            stdout=simulator_log_file,
            stderr=simulator_log_file,
            cwd=str(simulator_script.parent),
        )
        logger.info(f"Simulator started with PID {simulator_process.pid} (logging to {sim_log_path})")
        return {"message": "Simulator started", "pid": simulator_process.pid}
    except Exception as e:
        logger.error(f"Failed to start simulator: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start simulator: {str(e)}",
        )


@app.post("/api/simulator/stop", tags=["simulator"])
async def stop_simulator():
    """Stop the temperature sensor simulator process."""
    global simulator_process, simulator_log_file

    if not simulator_process or simulator_process.poll() is not None:
        raise HTTPException(status_code=400, detail="Simulator not running")

    try:
        simulator_process.terminate()
        simulator_process.wait(timeout=5)
        logger.info("Simulator stopped")
    except subprocess.TimeoutExpired:
        simulator_process.kill()
        simulator_process.wait()
        logger.warning("Simulator force-killed after timeout")
    except Exception as e:
        logger.error(f"Error stopping simulator: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error stopping simulator: {str(e)}")
    finally:
        if simulator_log_file:
            try:
                simulator_log_file.close()
                simulator_log_file = None
            except Exception:
                pass
    return {"message": "Simulator stopped"}


@app.post("/api/simulator/test-spike", tags=["simulator"])
async def test_spike():
    """
    Send a spike signal to the running simulator.

    Creates a signal file that the simulator reads on its next iteration,
    causing it to publish a temperature reading above the current threshold.
    The simulator will continue running and monitoring normally afterwards.
    """
    global simulator_process

    if not simulator_process or simulator_process.poll() is not None:
        raise HTTPException(status_code=400, detail="Simulator not running. Please start the simulator first.")

    current_threshold = mqtt_client.threshold if mqtt_client else app_config.get("default_threshold", 35.0)

    try:
        signal_file = _get_spike_signal_path()
        signal_file.write_text(str(current_threshold))
        logger.info(f"Spike signal written to {signal_file} with threshold {current_threshold}")
        return {
            "message": "Spike signal sent — temperature spike will be published and monitoring will continue",
            "threshold": current_threshold,
        }
    except Exception as e:
        logger.error(f"Error writing spike signal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error sending spike signal: {str(e)}")


@app.post("/api/alerts/test-email", tags=["alerts"])
async def test_email_alert():
    """Trigger a test alert email via SMTP to verify configuration."""
    global email_notifier, mqtt_client
    if not email_notifier:
        raise HTTPException(status_code=500, detail="Email notifier not initialized")

    threshold = mqtt_client.threshold if mqtt_client else 35.0
    from models import AlertEvent
    test_alert = AlertEvent(
        device_id="sensor-001",
        temperature=threshold + 6.2,
        threshold=threshold,
        alert_type="high_temperature",
        timestamp=datetime.utcnow().isoformat() + "Z",
        resolved=False,
    )
    email_notifier.send_alert_email(test_alert)
    return {
        "message": "Test alert email queued for sending",
        "recipient": email_notifier.recipient,
        "sender": email_notifier.user,
        "simulated_temperature": test_alert.temperature,
    }


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------

@app.websocket("/ws/temperature")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time temperature data streaming.

    Clients connect here to receive live temperature readings and alert events.
    Messages are JSON objects with 'type' ('temperature' or 'alert') and 'data' fields.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive - receive any client messages (currently not processed)
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
