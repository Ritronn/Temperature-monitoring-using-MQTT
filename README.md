# ThermosenseIoT Dashboard

Real-time temperature monitoring system demonstrating IoT communication patterns using MQTT protocol.

## Architecture Overview

```
[Sensor Simulator] → MQTT publish → [Eclipse Mosquitto Broker]
                                              ↓ MQTT subscribe
                                    [FastAPI Backend Service]
                                       ↙           ↘
                              [SQLite DB]      [WebSocket]
                                                    ↓
                                         [React Dashboard]
```

## Technology Stack

| Component        | Technology                                     |
|------------------|------------------------------------------------|
| Frontend         | React 18, Vite, Recharts, Lucide React, CSS    |
| Backend          | Python 3.11+, FastAPI, Uvicorn, Pydantic       |
| Database         | SQLite (via `sqlite3`)                         |
| Message Broker   | Eclipse Mosquitto 2.x (MQTT 3.1.1)             |
| MQTT Client      | Paho MQTT (`paho-mqtt`)                        |
| Protocol         | MQTT (port 1883), WebSocket (ws://), HTTP REST |

## Directory Structure

```
IOT/
├── .kiro/                      # Kiro spec files (requirements, design, tasks)
├── backend/                    # FastAPI backend service
│   ├── main.py                 # FastAPI app, all endpoints, startup/shutdown
│   ├── config.py               # Configuration loader with env overrides
│   ├── database.py             # SQLite DatabaseManager class
│   ├── models.py               # Pydantic data models (TemperatureReading, AlertEvent)
│   ├── mqtt_client.py          # MQTT subscriber with threshold checking
│   ├── websocket_manager.py    # WebSocket broadcast manager
│   ├── logging_config.py       # Rotating file + console logging setup
│   ├── requirements.txt        # Python dependencies
│   └── logs/                   # Log files (auto-created)
├── frontend/                   # React dashboard
│   ├── src/
│   │   ├── App.jsx             # Root component with dashboard layout
│   │   ├── App.css             # Design system CSS variables + base styles
│   │   ├── main.jsx            # Vite entry point
│   │   ├── components/
│   │   │   ├── Header.jsx          # Title + WebSocket connection status
│   │   │   ├── KPICards.jsx        # Current/avg/max temp + alert count
│   │   │   ├── LiveTemperature.jsx # Real-time temperature display
│   │   │   ├── TemperatureChart.jsx # Recharts historical graph
│   │   │   ├── AlertsPanel.jsx     # Alert events list
│   │   │   ├── RecentReadings.jsx  # Last 10 readings table
│   │   │   ├── SystemStatus.jsx    # Backend/MQTT/sensor status indicators
│   │   │   ├── ThresholdConfig.jsx # Threshold update form
│   │   │   └── SimulatorControls.jsx # Start/Stop/Spike buttons
│   │   ├── hooks/
│   │   │   └── useWebSocket.js     # Auto-reconnecting WebSocket hook
│   │   └── utils/
│   │       └── api.js              # HTTP API client functions
│   ├── package.json
│   └── vite.config.js
├── sensor/                     # Python sensor simulator
│   ├── simulator.py            # TemperatureSensor class + entry point
│   └── requirements.txt
├── mosquitto.conf              # Eclipse Mosquitto configuration
└── config.json                 # Shared system configuration
```

## Prerequisites

- **Python 3.11+** — `winget install Python.Python.3.11` or https://python.org
- **Node.js 18+** — `winget install OpenJS.NodeJS` or https://nodejs.org
- **Eclipse Mosquitto 2.x** — `winget install EclipseFoundation.Mosquitto` or https://mosquitto.org/download/

## Setup & Installation

Open **four separate PowerShell terminals** in the `IOT/` project root.

### Terminal 1 — MQTT Broker

```powershell
mosquitto -c mosquitto.conf -v
```

> Keep this running. You should see `mosquitto version 2.x starting`.

### Terminal 2 — Backend Service

```powershell
cd backend
python -m pip install -r requirements.txt
python main.py
```

> Or use uvicorn directly: `uvicorn main:app --host 0.0.0.0 --port 8000`
>
> Backend API docs available at: http://localhost:8000/docs

### Terminal 3 — Frontend Dashboard

```powershell
cd frontend
npm install
npm run dev
```

> Dashboard opens at: http://localhost:5173

### Terminal 4 — Sensor Simulator (optional — can also be started from the Dashboard)

```powershell
cd sensor
python -m pip install -r requirements.txt
python simulator.py --config ../config.json
```

## Startup Verification

After all services are running:

1. Open http://localhost:5173 in your browser
2. The header should show **"Live"** (green) WebSocket status
3. System Status card should show all three components **Online**
4. Temperature readings should appear every ~2 seconds
5. The chart should start plotting data

## Using the Dashboard

| Feature | How to use |
|---------|-----------|
| **Live Temperature** | Updates automatically every 2 seconds |
| **Historical Chart** | Click time window buttons: 5 min, 15 min, 1 hour, 24 hours |
| **Alert Threshold** | Enter a new value (0–100) and click Save |
| **Start/Stop Simulator** | Use the Simulator Control buttons |
| **Test Spike** | Click "Test Spike" — triggers a reading 5°C above threshold |
| **Alerts** | Red = active, Green = resolved; toggle "Show resolved" checkbox |

## Configuration (`config.json`)

```json
{
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
  }
}
```

## Graceful Shutdown

Recommended shutdown order:

1. **Sensor Simulator** — Press `Ctrl+C` in Terminal 4 (publishes offline status)
2. **Frontend** — Press `Ctrl+C` in Terminal 3
3. **Backend** — Press `Ctrl+C` in Terminal 2 (closes WebSocket + DB connections)
4. **MQTT Broker** — Press `Ctrl+C` in Terminal 1

## Troubleshooting

### MQTT Connection Failures

**Symptom**: Backend logs show `Failed to connect to MQTT broker`

- Verify Mosquitto is running: `netstat -an | findstr 1883`
- Check `mosquitto.conf` has `listener 1883 0.0.0.0` and `allow_anonymous true`
- Ensure no firewall is blocking port 1883
- Run Mosquitto with full logging: `mosquitto -c mosquitto.conf -v`

### Port Conflicts

**Symptom**: `Address already in use` error

- Backend (8000): `netstat -ano | findstr 8000` → `taskkill /PID <pid> /F`
- Frontend (5173): `netstat -ano | findstr 5173` → `taskkill /PID <pid> /F`
- MQTT (1883): `netstat -ano | findstr 1883` → `taskkill /PID <pid> /F`

### Missing Dependencies

**Python**: `python --version` should show 3.11+  
**Node.js**: `node --version` should show 18+  
**Mosquitto**: `mosquitto --version` should show 2.x

### Dashboard Shows "Reconnecting…"

- Check backend is running on port 8000: `curl http://localhost:8000/api/health`
- Check browser console for WebSocket errors (F12 → Console)
- CORS issues: ensure frontend is running on port 5173

### No Temperature Data Appearing

- Check simulator is running and connected to MQTT
- Verify backend is subscribed (look for log: `Subscribed to sensors/temperature`)
- Check the database path is writable (`thermosense.db` in project root)

### Database Errors

- The database `thermosense.db` is created automatically in the project root
- If corrupted, delete it and restart the backend: it will recreate the schema
