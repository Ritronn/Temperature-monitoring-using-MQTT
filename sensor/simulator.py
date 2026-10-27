"""
Temperature Sensor Simulator for ThermosenseIoT Dashboard

This module implements a Python MQTT temperature sensor simulator that:
- Connects to the MQTT broker and publishes temperature readings every 2 seconds
- Generates realistic random temperatures between 20-32°C (configurable)
- Supports spike generation via file-based IPC from the backend
- Publishes offline status on shutdown
- Handles SIGINT/SIGTERM for graceful shutdown
"""

import argparse
import json
import logging
import os
import random
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

from typing import Optional

import paho.mqtt.client as mqtt

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("thermosense.sensor")


# ---------------------------------------------------------------------------
# Spike signal path (must match backend/main.py)
# ---------------------------------------------------------------------------
def _get_spike_signal_path() -> Path:
    """Return platform-appropriate path for spike signal file."""
    temp_dir = os.environ.get("TEMP", os.environ.get("TMP", "/tmp"))
    return Path(temp_dir) / "thermosense_spike_signal.txt"


# ---------------------------------------------------------------------------
# Sensor class
# ---------------------------------------------------------------------------
class TemperatureSensor:
    """
    MQTT-based temperature sensor simulator.

    Generates simulated temperature readings and publishes them to the MQTT
    broker. Supports spike temperature generation triggered by a signal file.

    Attributes:
        device_id (str): Unique sensor identifier
        interval (float): Publish interval in seconds
        temp_min (float): Minimum normal temperature (°C)
        temp_max (float): Maximum normal temperature (°C)
        broker_host (str): MQTT broker hostname
        broker_port (int): MQTT broker port
        client: Paho MQTT client instance
        running (bool): Loop control flag
    """

    def __init__(self, config: dict):
        """
        Initialise sensor from configuration dictionary.

        Args:
            config: Sensor config with keys: device_id, publish_interval,
                    temperature_min, temperature_max, mqtt_broker_host,
                    mqtt_broker_port
        """
        sensor_cfg = config.get("sensor", {})

        self.device_id = sensor_cfg.get("device_id", "sensor-001")
        self.interval = sensor_cfg.get("publish_interval", 2.0)
        self.temp_min = sensor_cfg.get("temperature_min", 20.0)
        self.temp_max = sensor_cfg.get("temperature_max", 32.0)
        self.broker_host = config.get("mqtt_broker_host", "localhost")
        self.broker_port = int(config.get("mqtt_broker_port", 1883))
        self.running = False

        # Create MQTT client with MQTT 3.1.1 protocol
        self.client = mqtt.Client(
            client_id=self.device_id,
            protocol=mqtt.MQTTv311,
            clean_session=True,
        )
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect

        logger.info(
            f"TemperatureSensor initialised: device_id={self.device_id}, "
            f"interval={self.interval}s, range=[{self.temp_min}, {self.temp_max}]°C"
        )

    # ------------------------------------------------------------------
    # MQTT callbacks
    # ------------------------------------------------------------------

    def _on_connect(self, client, userdata, flags, rc):
        """Handle successful connection to MQTT broker."""
        if rc == 0:
            logger.info(f"[{self.device_id}] Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            # Publish online status
            status_msg = {
                "device_id": self.device_id,
                "status": "online",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            self.client.publish(
                "sensors/status",
                json.dumps(status_msg),
                qos=1,
                retain=True,
            )
        else:
            logger.error(f"[{self.device_id}] Connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Handle disconnection from MQTT broker."""
        if rc == 0:
            logger.info(f"[{self.device_id}] Cleanly disconnected from MQTT broker")
        else:
            logger.warning(
                f"[{self.device_id}] Unexpected disconnect (rc={rc}), "
                "paho will auto-reconnect..."
            )

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self) -> None:
        """
        Connect to the MQTT broker and start background network loop.

        Uses loop_start() so the network loop runs in a separate thread,
        allowing the main thread to continue generating readings. Paho
        handles automatic reconnection within loop_start().
        """
        logger.info(f"Connecting to MQTT broker at {self.broker_host}:{self.broker_port}")
        self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        self.client.loop_start()
        # Brief pause to allow on_connect to fire
        time.sleep(0.5)

    # ------------------------------------------------------------------
    # Temperature generation
    # ------------------------------------------------------------------

    def _generate_normal_temperature(self) -> float:
        """Generate a random temperature within the configured normal range."""
        return round(random.uniform(self.temp_min, self.temp_max), 2)

    def _generate_spike_temperature(self, threshold: float) -> float:
        """
        Generate a spike temperature guaranteed to be above threshold.

        Args:
            threshold: Current alert threshold in °C

        Returns:
            Temperature value at least 5°C above threshold
        """
        spike = threshold + 5.0 + random.uniform(0, 2)
        return round(spike, 2)

    def _check_spike_signal(self) -> Optional[float]:
        """
        Check for a spike signal file written by the backend.

        Returns:
            Threshold value read from signal file, or None if no signal.
        """
        signal_file = _get_spike_signal_path()
        if signal_file.exists():
            try:
                threshold_str = signal_file.read_text().strip()
                threshold = float(threshold_str)
                try:
                    signal_file.unlink(missing_ok=True)
                except Exception as unlink_err:
                    logger.debug(f"Could not immediately delete spike signal file: {unlink_err}")
                logger.info(f"[{self.device_id}] Spike signal received (threshold={threshold}°C)")
                return threshold
            except Exception as e:
                logger.error(f"[{self.device_id}] Error reading spike signal: {e}")
                try:
                    signal_file.unlink(missing_ok=True)
                except Exception:
                    pass
        return None

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        """
        Main publishing loop.

        Generates temperature readings and publishes them to MQTT every
        interval seconds. Checks for spike signals on each iteration.
        """
        self.running = True
        logger.info(f"[{self.device_id}] Starting temperature publishing loop")

        while self.running:
            try:
                # Check for spike signal
                spike_threshold = self._check_spike_signal()

                if spike_threshold is not None:
                    temperature = self._generate_spike_temperature(spike_threshold)
                    logger.info(f"[{self.device_id}] Publishing SPIKE temperature: {temperature}°C")
                else:
                    temperature = self._generate_normal_temperature()

                # Build reading payload
                reading = {
                    "device_id": self.device_id,
                    "temperature": temperature,
                    "unit": "C",
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                }

                # Publish with QoS 1
                result = self.client.publish(
                    "sensors/temperature",
                    json.dumps(reading),
                    qos=1,
                )

                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    logger.info(
                        f"[{self.device_id}] Published: {temperature}°C "
                        f"at {reading['timestamp']}"
                    )
                else:
                    logger.error(
                        f"[{self.device_id}] Publish failed with code: {result.rc}"
                    )

            except Exception as e:
                logger.error(f"[{self.device_id}] Error in publishing loop: {e}")

            # Sleep for publish interval
            time.sleep(self.interval)

        logger.info(f"[{self.device_id}] Publishing loop stopped")

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    def stop(self) -> None:
        """
        Gracefully stop the sensor.

        Publishes an offline status message, stops the MQTT loop,
        and disconnects from the broker.
        """
        logger.info(f"[{self.device_id}] Stopping sensor...")
        self.running = False

        # Publish offline status
        try:
            status_msg = {
                "device_id": self.device_id,
                "status": "offline",
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            self.client.publish(
                "sensors/status",
                json.dumps(status_msg),
                qos=1,
                retain=True,
            )
            # Brief wait for message to be sent
            time.sleep(0.3)
        except Exception as e:
            logger.error(f"[{self.device_id}] Error publishing offline status: {e}")

        # Stop loop and disconnect
        self.client.loop_stop()
        self.client.disconnect()
        logger.info(f"[{self.device_id}] Sensor stopped and disconnected")



# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def load_sensor_config(config_path: str) -> dict:
    """
    Load configuration from a JSON file.

    Args:
        config_path: Path to config.json

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}, using defaults")
        return {
            "mqtt_broker_host": "localhost",
            "mqtt_broker_port": 1883,
            "default_threshold": 35.0,
            "sensor": {
                "device_id": "sensor-001",
                "publish_interval": 2.0,
                "temperature_min": 20.0,
                "temperature_max": 32.0,
            },
        }
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        sys.exit(1)


def main():
    """Main entry point for the sensor simulator."""
    parser = argparse.ArgumentParser(description="ThermosenseIoT Sensor Simulator")
    parser.add_argument(
        "--config",
        default="../config.json",
        help="Path to config.json (default: ../config.json)",
    )
    args = parser.parse_args()

    # Resolve config path
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path(__file__).parent / args.config

    config = load_sensor_config(str(config_path))
    logger.info(f"Loaded configuration from {config_path}")

    # Create and start sensor
    sensor = TemperatureSensor(config)

    # Register shutdown signal handlers
    def _signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        sensor.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Connect and run
    try:
        sensor.connect()
        sensor.run()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received, stopping sensor...")
        sensor.stop()
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sensor.stop()
        sys.exit(1)


if __name__ == "__main__":
    main()
