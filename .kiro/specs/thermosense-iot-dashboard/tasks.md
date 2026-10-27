# Implementation Plan: ThermosenseIoT Dashboard

## Overview

This implementation plan breaks down the ThermosenseIoT Dashboard into actionable coding tasks. The system consists of four main components: an MQTT broker (Eclipse Mosquitto), a Python sensor simulator, a FastAPI backend service, and a React dashboard. Tasks are organized to allow incremental development with early validation of critical integration points.

## Tasks

- [x] 1. Project structure and configuration setup
  - Create root directory structure: `backend/`, `sensor/`, `frontend/`, project root files
  - Create `config.json` with all required fields: mqtt_broker_host, mqtt_broker_port, default_threshold, database_path, websocket_port, sensor configuration, logging configuration
  - Create `mosquitto.conf` with listener port 1883, allow_anonymous true, protocol_version mqttv311
  - Create Python requirements files for backend and sensor (`requirements.txt`)
  - Create frontend `package.json` with React 18, Vite, Recharts, Lucide React dependencies
  - _Requirements: 22.1, 22.2, 22.3, 24.4_

- [x] 2. Backend configuration loader module
  - [x] 2.1 Implement configuration loading and validation in `backend/config.py`
    - Create `load_config()` function that reads and validates config.json
    - Create default configuration if file doesn't exist
    - Validate required fields: mqtt_broker_host, mqtt_broker_port, default_threshold, database_path
    - Create `save_config_to_file()` function for persisting configuration changes
    - Support environment variable overrides for key settings
    - _Requirements: 22.1, 22.2, 22.3, 22.4_

  - [ ]* 2.2 Write unit tests for configuration module
    - Test loading valid configuration
    - Test creating default configuration when file missing
    - Test validation of invalid configuration values
    - Test environment variable overrides
    - _Requirements: 22.4_

- [x] 3. Backend logging setup
  - [x] 3.1 Implement logging configuration in backend
    - Create `setup_logging()` function in `backend/main.py` or separate logging module
    - Configure console handler with formatted output
    - Configure rotating file handler (max 10MB, keep 5 files)
    - Set log levels from configuration (default INFO)
    - Create logs directory if it doesn't exist
    - _Requirements: 23.7_

- [x] 4. Database layer implementation
  - [x] 4.1 Create database manager in `backend/database.py`
    - Create `DatabaseManager` class with initialization from config
    - Implement schema creation: temperature_readings table with indexes
    - Implement schema creation: alert_events table with indexes
    - Create connection using `check_same_thread=False` for thread safety
    - Implement `_initialize_db()` method to execute schema SQL
    - _Requirements: 4.1, 4.2, 4.3, 4.5_

  - [x] 4.2 Implement database write operations
    - Implement `insert_reading(reading)` with parameterized query
    - Implement `insert_alert(alert)` with duplicate checking logic
    - Implement `resolve_alerts(device_id)` to mark alerts as resolved
    - All operations use parameterized queries to prevent SQL injection
    - _Requirements: 4.4, 6.2, 6.3, 6.4, 6.6_

  - [x] 4.3 Implement database query operations
    - Implement `get_readings_history(start_time, end_time, device_id)` with indexed query
    - Implement `get_latest_readings()` to fetch most recent reading per device
    - Implement `get_alerts(resolved)` with optional filter
    - Implement `get_readings_since(cutoff_time)` for status checks
    - _Requirements: 7.3, 7.4, 7.5_

  - [x] 4.4 Implement data retention and cleanup
    - Implement `cleanup_old_readings(days)` to delete old temperature readings
    - Default retention period: 7 days
    - Use parameterized query with timestamp cutoff
    - _Requirements: 4.6_

  - [ ]* 4.5 Write unit tests for database operations
    - Test schema creation and initialization
    - Test inserting and querying temperature readings
    - Test alert creation and resolution logic
    - Test duplicate alert prevention
    - Test data cleanup functionality
    - Use in-memory SQLite database for tests
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

- [x] 5. Backend data models
  - [x] 5.1 Define Pydantic models in `backend/models.py`
    - Create `TemperatureReading` model with validation: device_id (str, max 100), temperature (float, -50 to 150), unit (C/F/K), timestamp (ISO 8601)
    - Create `AlertEvent` model with validation: device_id, temperature, threshold, alert_type, timestamp, resolved (bool)
    - Create `ConfigUpdate` model for threshold configuration (float, 0 to 100)
    - Add custom validators for timestamp format validation
    - Add schema examples for API documentation
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5_

  - [ ]* 5.2 Write unit tests for Pydantic models
    - Test valid model instantiation with correct data
    - Test validation errors for out-of-range temperature values
    - Test validation errors for invalid device_id (empty, too long)
    - Test validation errors for invalid unit values
    - Test validation errors for invalid timestamp formats
    - Test threshold validation (negative values, above 100)
    - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5, 25.6_

- [ ] 6. Checkpoint - Ensure database and models work correctly
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. WebSocket manager implementation
  - [x] 7.1 Create WebSocket manager in `backend/websocket_manager.py`
    - Create `WebSocketManager` class with set of active connections
    - Implement `connect(websocket)` to accept and track connections
    - Implement `disconnect(websocket)` to remove connections
    - Implement `broadcast_reading(reading)` to send temperature updates
    - Implement `broadcast_alert(alert)` to send alert notifications
    - Implement `_broadcast(message)` with error handling and cleanup of disconnected clients
    - Format messages as JSON with "type" and "data" fields
    - Store reference to asyncio event loop for thread-safe broadcasting
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [ ]* 7.2 Write unit tests for WebSocket manager
    - Test connection tracking (adding and removing clients)
    - Test broadcasting to multiple clients
    - Test handling of disconnected clients during broadcast
    - Test message formatting for temperature and alert types
    - Use mock WebSocket objects for testing
    - _Requirements: 5.3, 5.4, 5.5_

- [ ] 8. MQTT client component
  - [x] 8.1 Implement MQTT client in `backend/mqtt_client.py`
    - Create `MQTTClient` class with config, database manager, and WebSocket manager dependencies
    - Implement `connect()` to establish connection with callbacks
    - Implement `_on_connect()` callback to subscribe to sensors/temperature and sensors/status with QoS 1
    - Implement `_on_disconnect()` callback with reconnection logging
    - Use `client.loop_start()` to run MQTT in separate thread
    - Store connection state and current threshold
    - _Requirements: 3.1, 3.5, 5.6, 23.1_

  - [x] 8.2 Implement MQTT message processing
    - Implement `_on_message()` callback to route messages by topic
    - Implement `_handle_temperature_reading()` to validate, persist, check threshold, and broadcast
    - Implement threshold checking logic: create alert if temperature > threshold
    - Implement alert resolution logic: resolve alerts if temperature <= threshold
    - Use `asyncio.run_coroutine_threadsafe()` to bridge MQTT thread with asyncio WebSocket manager
    - Handle JSON parsing errors and validation errors gracefully (log and continue)
    - _Requirements: 3.2, 3.3, 3.4, 6.1, 6.2, 6.3, 6.4, 6.5, 20.1_

  - [x] 8.3 Implement graceful MQTT disconnect
    - Implement `disconnect()` method to stop loop and close connection
    - Call `client.loop_stop()` then `client.disconnect()`
    - _Requirements: 3.6, 21.2_

  - [ ]* 8.4 Write unit tests for MQTT client
    - Test connection and subscription logic
    - Test message validation and processing
    - Test threshold checking and alert creation
    - Test alert resolution when temperature normalizes
    - Test error handling for invalid messages
    - Use mock MQTT client and mock dependencies
    - _Requirements: 3.2, 3.3, 6.2, 6.3, 6.4, 20.1_

- [x] 9. FastAPI application and HTTP endpoints
  - [ ] 9.1 Create FastAPI app skeleton in `backend/main.py`
    - Create FastAPI application instance with title and version
    - Define startup event handler to initialize components
    - Define shutdown event handler to cleanup resources
    - Set up CORS middleware if needed for frontend development
    - _Requirements: 21.1, 21.2, 21.3_

  - [x] 9.2 Implement health and status endpoints
    - Implement GET `/api/health` returning {"status": "healthy"}
    - Implement GET `/api/status` returning mqtt_connected, sensor_online, backend_uptime_seconds
    - Calculate sensor_online by checking for recent readings (within 30 seconds)
    - _Requirements: 7.1, 7.2, 23.4_

  - [x] 9.3 Implement readings query endpoints
    - Implement GET `/api/readings/latest` returning most recent reading per device
    - Implement GET `/api/readings/history` with query params: start_time, end_time, device_id (optional)
    - Validate ISO 8601 timestamp format for history endpoint
    - Return HTTP 400 for invalid timestamp formats
    - _Requirements: 7.3, 7.4, 25.4, 25.6_

  - [x] 9.4 Implement alerts and configuration endpoints
    - Implement GET `/api/alerts` with optional query param "resolved" (boolean)
    - Implement GET `/api/config` returning current threshold
    - Implement PUT `/api/config` accepting JSON with threshold field
    - Validate threshold range (0-100), return HTTP 400 for invalid values
    - Persist threshold changes using `save_config_to_file()`
    - _Requirements: 7.5, 7.6, 7.7, 7.8, 25.5, 25.6_

  - [x] 9.5 Implement WebSocket endpoint
    - Implement WebSocket endpoint at `/ws/temperature`
    - Accept connection using WebSocket manager
    - Keep connection alive with infinite loop and `receive_text()`
    - Handle `WebSocketDisconnect` exception to cleanup
    - _Requirements: 5.1, 5.2_

  - [ ]* 9.6 Write integration tests for HTTP endpoints
    - Test health endpoint returns 200
    - Test status endpoint returns correct structure
    - Test latest readings endpoint
    - Test history endpoint with valid time ranges
    - Test history endpoint rejects invalid timestamps
    - Test alerts endpoint with resolved filter
    - Test config GET and PUT endpoints
    - Test config validation (invalid threshold values)
    - Use FastAPI TestClient for all tests
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 25.6_

- [x] 10. Simulator control endpoints
  - [x] 10.1 Implement simulator control in `backend/main.py`
    - Implement POST `/api/simulator/start` to spawn simulator subprocess
    - Implement POST `/api/simulator/stop` to terminate simulator process
    - Implement POST `/api/simulator/test-spike` to create spike signal file
    - Track simulator process in app state
    - Return HTTP 400 if start called when already running
    - Return HTTP 400 if stop called when not running
    - Return HTTP 500 if process spawn fails with error details
    - Write spike signal to `/tmp/thermosense_spike_signal.txt` (or Windows equivalent temp path)
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ]* 10.2 Write integration tests for simulator control
    - Test starting simulator successfully
    - Test error when starting already-running simulator
    - Test stopping simulator
    - Test error when stopping non-running simulator
    - Test spike signal file creation
    - Use mock subprocess for tests
    - _Requirements: 8.4, 8.5, 8.6_

- [ ] 11. Backend startup and shutdown handlers
  - [x] 11.1 Complete startup event handler
    - Record start time for uptime calculation
    - Load configuration using config module
    - Initialize DatabaseManager with database path from config
    - Initialize WebSocketManager and store asyncio event loop reference
    - Initialize MQTTClient with config, database, and WebSocket manager
    - Connect MQTT client
    - Start background cleanup task with `asyncio.create_task()`
    - Log startup completion
    - _Requirements: 3.1, 4.1, 5.2, 23.1_

  - [x] 11.2 Implement cleanup background task
    - Create async function that runs infinite loop
    - Sleep for 86400 seconds (24 hours) between iterations
    - Call `db.cleanup_old_readings(days=7)` on each iteration
    - _Requirements: 4.6_

  - [x] 11.3 Complete shutdown event handler
    - Close all active WebSocket connections
    - Disconnect MQTT client gracefully
    - Close database connection
    - Terminate simulator process if running
    - Log shutdown completion
    - _Requirements: 21.1, 21.2, 21.3, 21.4_

- [ ] 12. Checkpoint - Ensure backend service runs and connects
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Python sensor simulator implementation
  - [ ] 13.1 Create sensor simulator in `sensor/simulator.py`
    - Create `TemperatureSensor` class with configuration parameters
    - Initialize MQTT client with device_id from config
    - Store configuration: publish_interval, temperature_min, temperature_max
    - Create `connect()` method to connect to broker and start loop
    - Implement `_on_connect()` callback to log connection status
    - Implement `_on_disconnect()` callback to log disconnect and rely on auto-reconnect
    - _Requirements: 1.1, 1.5, 22.5_

  - [ ] 13.2 Implement temperature generation and publishing
    - Create `run()` method with infinite loop
    - Generate random temperature between min and max
    - Check for spike signal file on each iteration
    - If spike signal exists, read threshold and generate spike temperature (threshold + 5 + random(0, 2))
    - Delete spike signal file after reading
    - Format reading as JSON with device_id, temperature, unit, timestamp (ISO 8601)
    - Publish to "sensors/temperature" topic with QoS 1
    - Log publish failures if result.rc != MQTT_ERR_SUCCESS
    - Sleep for publish_interval seconds
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 9.1, 9.2, 9.3, 9.4, 23.5_

  - [ ] 13.3 Implement graceful shutdown
    - Create `stop()` method to set running flag to False
    - Publish status message to "sensors/status" with status "offline"
    - Stop MQTT loop and disconnect
    - Handle SIGINT and SIGTERM signals to call stop()
    - _Requirements: 1.6, 21.4_

  - [ ] 13.4 Add simulator main entry point
    - Load configuration from config.json
    - Setup logging for simulator
    - Create TemperatureSensor instance
    - Connect to broker
    - Run sensor loop
    - Handle KeyboardInterrupt for clean exit
    - _Requirements: 22.5, 23.5_

  - [ ]* 13.5 Write unit tests for sensor simulator
    - Test temperature generation within range
    - Test spike temperature generation above threshold
    - Test MQTT message format and QoS level
    - Test offline status message on shutdown
    - Use mock MQTT client for tests
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.6, 9.1, 9.2_

- [ ] 14. Checkpoint - Ensure sensor connects and publishes
  - Ensure all tests pass, ask the user if questions arise.

- [x] 15. React frontend project setup
  - [x] 15.1 Initialize React project with Vite
    - Create frontend directory and initialize with Vite using React template
    - Install dependencies: react, react-dom, recharts, lucide-react
    - Configure Vite for development (vite.config.js)
    - Create index.html entry point
    - Create src/main.jsx to render App component
    - _Requirements: 24.3_

  - [x] 15.2 Create CSS design system in `src/App.css`
    - Define CSS variables for colors (dark theme: navy/charcoal backgrounds)
    - Define CSS variables for spacing (xs, sm, md, lg, xl)
    - Define CSS variables for border-radius and shadows
    - Define CSS variables for typography (font-family, font-sizes)
    - Create reusable classes: .card, .button, .button-primary, .button-success, .button-danger
    - Create status indicator classes: .status-indicator, .status-online, .status-offline
    - Create responsive grid layout with media queries: mobile (1 col), tablet (2 col), desktop (3 col)
    - Ensure minimum touch target size 44x44px for buttons
    - _Requirements: 18.4, 19.1, 19.2, 19.3, 19.4, 19.5_

- [x] 16. Frontend HTTP API client
  - [x] 16.1 Create API client utilities in `src/utils/api.js`
    - Define API_BASE_URL constant (http://localhost:8000)
    - Implement `fetchHealth()` for GET /api/health
    - Implement `fetchStatus()` for GET /api/status
    - Implement `fetchLatestReadings()` for GET /api/readings/latest
    - Implement `fetchReadingsHistory(startTime, endTime, deviceId)` for GET /api/readings/history
    - Implement `fetchAlerts(resolved)` for GET /api/alerts
    - Implement `fetchConfig()` for GET /api/config
    - Implement `updateConfig(threshold)` for PUT /api/config
    - Implement `startSimulator()` for POST /api/simulator/start
    - Implement `stopSimulator()` for POST /api/simulator/stop
    - Implement `testSpike()` for POST /api/simulator/test-spike
    - Handle HTTP errors and throw with descriptive messages
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 8.1, 8.2, 8.3_

- [x] 17. WebSocket connection hook
  - [x] 17.1 Create useWebSocket custom hook in `src/hooks/useWebSocket.js`
    - Create custom hook that accepts WebSocket URL
    - Use useRef to store WebSocket instance
    - Use useState for connection status and last message
    - Implement connection logic in useEffect
    - Handle onopen event to set connection status
    - Handle onmessage event to parse JSON and update state
    - Handle onerror event to log errors
    - Handle onclose event to attempt reconnection after 3 seconds
    - Return { isConnected, lastMessage } from hook
    - Cleanup WebSocket and timeout on unmount
    - _Requirements: 5.2, 10.1, 10.5, 10.6, 20.3_

- [ ] 18. Dashboard core layout and App component
  - [ ] 18.1 Create App component in `src/App.jsx`
    - Initialize WebSocket connection using useWebSocket hook
    - Create state for: currentReading, alerts, readings, system status
    - Listen to lastMessage from WebSocket and update state based on message type
    - Add temperature readings to readings list (keep last 10)
    - Add alert events to alerts list
    - Create dashboard grid layout structure
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 18.1, 18.2_

  - [ ] 18.2 Create Header component in `src/components/Header.jsx`
    - Display application title and branding
    - Simple header with styling using design system
    - _Requirements: 19.4_

- [ ] 19. System status and connection indicators
  - [ ] 19.1 Create SystemStatus component in `src/components/SystemStatus.jsx`
    - Display connection status for backend, MQTT broker, sensor
    - Poll /api/status every 5 seconds using setInterval
    - Display green indicator when connected/online
    - Display red indicator when disconnected/offline
    - Display backend uptime in human-readable format
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ] 20. KPI cards component
  - [ ] 20.1 Create KPICards component in `src/components/KPICards.jsx`
    - Accept props: currentReading, readings, alerts
    - Display card for Current Temperature from currentReading
    - Calculate and display Average Temperature from readings array
    - Calculate and display Maximum Temperature from readings array
    - Display Alert Count as number of unresolved alerts
    - Update values when props change
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5_

- [ ] 21. Live temperature display
  - [ ] 21.1 Create LiveTemperature component in `src/components/LiveTemperature.jsx`
    - Accept currentReading as prop
    - Display temperature value rounded to 1 decimal place with unit symbol (°C)
    - Display timestamp in human-readable format
    - Highlight value with large font size for visibility
    - Update within 100ms of receiving new reading
    - _Requirements: 10.2, 10.3, 10.4_

- [ ] 22. Temperature chart with historical data
  - [ ] 22.1 Create TemperatureChart component in `src/components/TemperatureChart.jsx`
    - Import Recharts components: LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine
    - Define time window options: 5min, 15min, 1hour, 24hours
    - Create state for selectedWindow and chartData
    - Implement `loadHistoricalData()` to fetch data for selected window
    - Implement `downsample()` function to reduce data to max 500 points
    - Implement `formatTime()` to format ISO timestamps for display
    - Add new readings from WebSocket to chart data
    - Display time window selection buttons
    - Render LineChart with temperature data, threshold reference line
    - Disable animations with `isAnimationActive={false}` for performance
    - Use responsive container with 100% width and fixed height
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7_

- [ ] 23. Alerts panel component
  - [ ] 23.1 Create AlertsPanel component in `src/components/AlertsPanel.jsx`
    - Fetch alerts from /api/alerts on component mount
    - Display list of alert events (both resolved and unresolved)
    - Show device_id, temperature, threshold, alert_type, timestamp, resolved status for each alert
    - Use red indicator for unresolved alerts
    - Use green indicator for resolved alerts
    - Update alerts list when new alert received via WebSocket
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [ ] 24. Recent readings table
  - [ ] 24.1 Create RecentReadings component in `src/components/RecentReadings.jsx`
    - Display table with columns: timestamp, device_id, temperature, unit
    - Show 10 most recent readings
    - Add new readings to top of table when received via WebSocket
    - Remove oldest entry if table exceeds 10 rows
    - _Requirements: 17.1, 17.2, 17.3, 17.4_

- [ ] 25. Threshold configuration control
  - [ ] 25.1 Create ThresholdConfig component in `src/components/ThresholdConfig.jsx`
    - Fetch current threshold from /api/config on mount
    - Display input field with current threshold value
    - Display "Save" button to submit changes
    - Validate input is number between 0 and 100
    - Send PUT request to /api/config on submit
    - Display success message on successful update
    - Display error message and revert value on failure
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6_

- [ ] 26. Simulator control buttons
  - [ ] 26.1 Create SimulatorControls component in `src/components/SimulatorControls.jsx`
    - Display three buttons: "Start Simulator", "Stop Simulator", "Test Spike"
    - Implement click handlers to call corresponding API functions
    - Disable "Start" button when simulator status is "online"
    - Disable "Stop" and "Test Spike" buttons when simulator status is "offline"
    - Display error messages when API calls fail
    - Get simulator status from parent component or system status API
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7_

- [ ] 27. Error handling and display
  - [ ] 27.1 Add error handling to all components
    - Wrap API calls in try-catch blocks
    - Display error messages using consistent UI pattern
    - Provide retry buttons for failed operations
    - Add error boundary component for chart rendering errors
    - Show connection status when WebSocket disconnects
    - _Requirements: 20.2, 20.3, 20.4_

- [ ] 28. Responsive layout integration
  - [ ] 28.1 Integrate all components in App.jsx with responsive grid
    - Arrange components in dashboard grid layout
    - Apply responsive CSS classes for mobile/tablet/desktop
    - Test layout at various viewport widths (320px, 768px, 1200px, 2560px)
    - Ensure cards stack vertically on mobile
    - Ensure multi-column layout on tablet and desktop
    - _Requirements: 18.1, 18.2, 18.3, 18.5_

- [ ] 29. Checkpoint - Ensure dashboard displays data correctly
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 30. Integration testing across components
  - [ ]* 30.1 Write end-to-end test for temperature monitoring flow
    - Start MQTT broker, backend, and simulator
    - Verify sensor publishes messages
    - Verify backend receives and persists data
    - Verify WebSocket broadcasts to connected clients
    - Verify dashboard receives and displays temperature updates
    - _Requirements: 1.1, 3.2, 3.4, 5.3, 10.2_

  - [ ]* 30.2 Write end-to-end test for alert generation
    - Start all components with threshold configured
    - Trigger temperature spike via API
    - Verify alert is created in database
    - Verify alert is broadcast via WebSocket
    - Verify alert appears in dashboard alerts panel
    - Verify alert is resolved when temperature normalizes
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 9.2, 12.3_

  - [ ]* 30.3 Write end-to-end test for historical data query
    - Populate database with historical readings
    - Request data via /api/readings/history with time range
    - Verify correct data is returned
    - Verify dashboard chart displays historical data
    - _Requirements: 7.4, 11.3_

  - [ ]* 30.4 Write end-to-end test for threshold configuration
    - Update threshold via dashboard
    - Verify PUT /api/config succeeds
    - Verify new threshold persisted to config.json
    - Trigger temperature spike above new threshold
    - Verify alert is created based on new threshold
    - _Requirements: 7.7, 7.8, 14.3, 14.4, 6.2_

  - [ ]* 30.5 Write end-to-end test for simulator control
    - Start simulator via /api/simulator/start
    - Verify simulator process is running
    - Verify temperature readings appear in backend
    - Stop simulator via /api/simulator/stop
    - Verify offline status message received
    - Verify readings stop appearing
    - _Requirements: 8.1, 8.2, 1.1, 1.6_

- [ ] 31. Documentation and setup guide
  - [ ] 31.1 Create comprehensive README.md
    - Document system overview and architecture
    - List prerequisites: Python 3.11+, Node.js 18+, Eclipse Mosquitto
    - Provide Windows PowerShell installation commands for all dependencies
    - Document complete directory structure with descriptions
    - Provide startup sequence with commands for each terminal window
    - Document verification steps after startup
    - Document graceful shutdown sequence
    - Create troubleshooting section: MQTT connection failures, port conflicts, missing dependencies
    - List complete technology stack with versions
    - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 24.6_

  - [ ] 31.2 Add code comments and docstrings
    - Add module-level docstrings for all Python files
    - Add docstrings for all classes and public methods
    - Add JSDoc comments for key frontend functions
    - Document complex algorithms (downsampling, threshold logic)
    - _Requirements: 24.1_

- [ ] 32. Final system verification
  - [ ] 32.1 Complete system startup and verification
    - Start all components in correct order: broker, backend, simulator, frontend
    - Verify MQTT broker logs show connections
    - Verify backend logs show MQTT subscription and WebSocket endpoint
    - Verify simulator logs show publishing events
    - Verify dashboard loads without console errors
    - Verify real-time data flows through entire pipeline
    - Test all user interactions: threshold config, simulator control, time window selection
    - _Requirements: 1.1, 3.1, 5.1, 10.1, 13.1, 23.1, 23.4_

  - [ ] 32.2 Graceful shutdown verification
    - Shutdown components in recommended order
    - Verify offline status message published by simulator
    - Verify backend closes WebSocket connections cleanly
    - Verify backend disconnects from MQTT broker
    - Verify no error messages during shutdown sequence
    - _Requirements: 21.1, 21.2, 21.3, 21.4_

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP delivery
- Each task references specific requirements from requirements.md for traceability
- The implementation uses Python for backend/simulator and JavaScript (not TypeScript) for frontend
- The system is designed for Windows development environment using PowerShell
- CSS uses vanilla styles with design system variables (no Tailwind CSS)
- Critical integration points (MQTT, WebSocket, Database) are validated early with checkpoints
- Testing focuses on unit tests for core logic and integration tests for critical flows
- All components include proper error handling and logging for troubleshooting

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1.1"]
    },
    {
      "id": 1,
      "tasks": ["2.1", "3.1", "15.1"]
    },
    {
      "id": 2,
      "tasks": ["2.2", "4.1", "5.1", "15.2"]
    },
    {
      "id": 3,
      "tasks": ["4.2", "4.3", "4.4", "5.2", "16.1", "17.1"]
    },
    {
      "id": 4,
      "tasks": ["4.5", "7.1"]
    },
    {
      "id": 5,
      "tasks": ["7.2", "8.1"]
    },
    {
      "id": 6,
      "tasks": ["8.2", "8.3", "18.1", "18.2"]
    },
    {
      "id": 7,
      "tasks": ["8.4", "9.1"]
    },
    {
      "id": 8,
      "tasks": ["9.2", "9.3", "9.4", "9.5", "19.1", "20.1", "21.1"]
    },
    {
      "id": 9,
      "tasks": ["9.6", "10.1", "22.1", "23.1", "24.1", "25.1", "26.1"]
    },
    {
      "id": 10,
      "tasks": ["10.2", "11.1", "11.2", "11.3", "27.1"]
    },
    {
      "id": 11,
      "tasks": ["13.1"]
    },
    {
      "id": 12,
      "tasks": ["13.2", "13.3", "13.4"]
    },
    {
      "id": 13,
      "tasks": ["13.5", "28.1"]
    },
    {
      "id": 14,
      "tasks": ["30.1", "30.2", "30.3", "30.4", "30.5", "31.1", "31.2"]
    },
    {
      "id": 15,
      "tasks": ["32.1", "32.2"]
    }
  ]
}
```
