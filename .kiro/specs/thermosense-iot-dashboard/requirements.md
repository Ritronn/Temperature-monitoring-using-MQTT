# Requirements Document

## Introduction

The ThermosenseIoT Dashboard is a real-time temperature monitoring system that demonstrates IoT communication patterns using MQTT protocol. The system consists of a Python-based temperature sensor simulator, an MQTT message broker, a FastAPI backend service, and a React-based web dashboard. The system enables monitoring of temperature data streams, historical analysis, threshold-based alerting, and remote sensor control.

## Glossary

- **Sensor_Simulator**: Python application that generates and publishes simulated temperature readings via MQTT
- **MQTT_Broker**: Eclipse Mosquitto message broker that routes messages between publishers and subscribers
- **Backend_Service**: FastAPI application that subscribes to MQTT messages, persists data, and provides HTTP/WebSocket APIs
- **Dashboard**: React.js web application that displays real-time and historical temperature data
- **Temperature_Reading**: Data structure containing device_id, temperature value, unit, and timestamp
- **Alert_Event**: Notification triggered when temperature exceeds or falls below configured threshold
- **WebSocket_Connection**: Bidirectional communication channel between Backend_Service and Dashboard
- **Threshold**: Configurable temperature limit that triggers Alert_Events
- **Database**: SQLite database storing Temperature_Readings and Alert_Events
- **QoS**: Quality of Service level for MQTT message delivery (0=at most once, 1=at least once, 2=exactly once)

## Requirements

### Requirement 1: MQTT Message Publishing

**User Story:** As a sensor simulator, I want to publish temperature readings via MQTT, so that the backend service can receive and process the data.

#### Acceptance Criteria

1. WHEN the Sensor_Simulator is started, THE Sensor_Simulator SHALL publish a Temperature_Reading to topic "sensors/temperature" every 2 seconds (±0.5 seconds)
2. THE Sensor_Simulator SHALL format Temperature_Reading as JSON with fields: device_id (string), temperature (float), unit (string), timestamp (ISO 8601 string)
3. THE Sensor_Simulator SHALL publish Temperature_Readings with QoS level 1
4. THE Sensor_Simulator SHALL generate temperature values between 20.0°C and 32.0°C during normal operation
5. WHEN the MQTT_Broker connection is lost, THE Sensor_Simulator SHALL attempt reconnection every 5 seconds for up to 10 attempts
6. WHEN the Sensor_Simulator is stopped, THE Sensor_Simulator SHALL publish a status message to topic "sensors/status" with payload containing device_id and status "offline"

### Requirement 2: MQTT Broker Configuration

**User Story:** As a system operator, I want a properly configured MQTT broker, so that messages are reliably routed between components.

#### Acceptance Criteria

1. THE MQTT_Broker SHALL listen for connections on port 1883
2. THE MQTT_Broker SHALL support MQTT protocol version 3.1.1
3. THE MQTT_Broker SHALL allow anonymous connections (no authentication required)
4. THE MQTT_Broker SHALL retain the last message published to topic "sensors/status"
5. THE MQTT_Broker SHALL accept connections from localhost

### Requirement 3: Backend MQTT Subscription

**User Story:** As a backend service, I want to subscribe to MQTT temperature messages, so that I can process and store the data.

#### Acceptance Criteria

1. WHEN the Backend_Service starts, THE Backend_Service SHALL subscribe to topic "sensors/temperature" with QoS level 1
2. WHEN a message is received on "sensors/temperature", THE Backend_Service SHALL validate the JSON payload contains required fields: device_id, temperature, unit, timestamp
3. IF the JSON payload is invalid or missing required fields, THEN THE Backend_Service SHALL log the error and discard the message
4. WHEN a valid Temperature_Reading is received, THE Backend_Service SHALL persist it to the Database within 100 milliseconds
5. WHEN the MQTT_Broker connection is lost, THE Backend_Service SHALL attempt reconnection every 5 seconds indefinitely
6. WHEN the Backend_Service stops, THE Backend_Service SHALL unsubscribe from all topics and close the MQTT connection gracefully

### Requirement 4: Database Persistence

**User Story:** As a backend service, I want to store temperature readings in a database, so that historical data can be queried and analyzed.

#### Acceptance Criteria

1. THE Backend_Service SHALL create a SQLite database file named "thermosense.db" if it does not exist
2. THE Database SHALL contain a table "temperature_readings" with columns: id (integer primary key), device_id (text), temperature (real), unit (text), timestamp (text)
3. THE Database SHALL contain a table "alert_events" with columns: id (integer primary key), device_id (text), temperature (real), threshold (real), alert_type (text), timestamp (text), resolved (boolean)
4. WHEN persisting a Temperature_Reading, THE Backend_Service SHALL use parameterized SQL queries to prevent SQL injection
5. THE Backend_Service SHALL create database indexes on timestamp columns for query performance
6. THE Database SHALL persist Temperature_Readings for at least 7 days before automatic cleanup

### Requirement 5: Real-Time WebSocket Broadcasting

**User Story:** As a dashboard user, I want to receive live temperature updates, so that I can monitor sensor data in real-time.

#### Acceptance Criteria

1. THE Backend_Service SHALL provide a WebSocket endpoint at "/ws/temperature"
2. WHEN a client connects to "/ws/temperature", THE Backend_Service SHALL accept the WebSocket connection
3. WHEN a valid Temperature_Reading is received via MQTT, THE Backend_Service SHALL broadcast the reading to all connected WebSocket clients within 50 milliseconds
4. THE Backend_Service SHALL format WebSocket messages as JSON containing the complete Temperature_Reading
5. WHEN a WebSocket client disconnects, THE Backend_Service SHALL remove the client from the broadcast list and release associated resources
6. THE Backend_Service SHALL support at least 10 concurrent WebSocket connections

### Requirement 6: Temperature Threshold Alerts

**User Story:** As a monitoring operator, I want to receive alerts when temperature exceeds thresholds, so that I can respond to anomalous conditions.

#### Acceptance Criteria

1. THE Backend_Service SHALL maintain a configurable Threshold value (default 35.0°C)
2. WHEN a Temperature_Reading exceeds the Threshold, THE Backend_Service SHALL create an Alert_Event with alert_type "high_temperature"
3. WHEN a Temperature_Reading falls below the Threshold after an Alert_Event was created, THE Backend_Service SHALL mark the Alert_Event as resolved
4. THE Backend_Service SHALL create only one unresolved Alert_Event per device_id at any time (no duplicate alerts)
5. WHEN an Alert_Event is created, THE Backend_Service SHALL broadcast the alert to all WebSocket clients
6. THE Backend_Service SHALL persist all Alert_Events to the Database

### Requirement 7: HTTP API Endpoints

**User Story:** As a dashboard application, I want to query temperature data and system status via HTTP, so that I can display current and historical information.

#### Acceptance Criteria

1. THE Backend_Service SHALL provide a GET endpoint "/api/health" that returns HTTP status 200 and JSON payload {"status": "healthy"}
2. THE Backend_Service SHALL provide a GET endpoint "/api/status" that returns MQTT connection status, sensor online status, and backend uptime
3. THE Backend_Service SHALL provide a GET endpoint "/api/readings/latest" that returns the most recent Temperature_Reading for each device_id
4. THE Backend_Service SHALL provide a GET endpoint "/api/readings/history" with query parameters: start_time, end_time, device_id (optional), that returns Temperature_Readings within the time range
5. THE Backend_Service SHALL provide a GET endpoint "/api/alerts" with optional query parameter "resolved" that returns Alert_Events filtered by resolution status
6. THE Backend_Service SHALL provide a GET endpoint "/api/config" that returns current Threshold configuration
7. THE Backend_Service SHALL provide a PUT endpoint "/api/config" that accepts JSON payload with "threshold" field and updates the Threshold value
8. IF the Threshold value is below 0 or above 100, THEN THE Backend_Service SHALL return HTTP status 400 with error message

### Requirement 8: Simulator Remote Control

**User Story:** As a dashboard user, I want to control the sensor simulator remotely, so that I can start, stop, and test the system without accessing the simulator directly.

#### Acceptance Criteria

1. THE Backend_Service SHALL provide a POST endpoint "/api/simulator/start" that starts the Sensor_Simulator process
2. THE Backend_Service SHALL provide a POST endpoint "/api/simulator/stop" that stops the Sensor_Simulator process gracefully
3. THE Backend_Service SHALL provide a POST endpoint "/api/simulator/test-spike" that signals the Sensor_Simulator to generate one Temperature_Reading above the Threshold
4. WHEN "/api/simulator/start" is called and the Sensor_Simulator is already running, THE Backend_Service SHALL return HTTP status 400 with message "Simulator already running"
5. WHEN "/api/simulator/stop" is called and the Sensor_Simulator is not running, THE Backend_Service SHALL return HTTP status 400 with message "Simulator not running"
6. WHEN the Sensor_Simulator process fails to start, THE Backend_Service SHALL return HTTP status 500 with error details

### Requirement 9: Spike Simulation

**User Story:** As a system tester, I want to trigger temperature spikes on demand, so that I can verify alert functionality.

#### Acceptance Criteria

1. WHEN the Sensor_Simulator receives a spike signal, THE Sensor_Simulator SHALL generate one Temperature_Reading with value at least 5°C above the current Threshold
2. THE Sensor_Simulator SHALL publish the spike Temperature_Reading to topic "sensors/temperature" within 1 second of receiving the signal
3. AFTER publishing a spike Temperature_Reading, THE Sensor_Simulator SHALL resume normal temperature generation (20-32°C range)
4. THE Sensor_Simulator SHALL accept spike signals via file-based IPC or socket communication from the Backend_Service

### Requirement 10: Dashboard Live Data Display

**User Story:** As a dashboard user, I want to see current temperature readings in real-time, so that I can monitor the system continuously.

#### Acceptance Criteria

1. THE Dashboard SHALL establish a WebSocket connection to "/ws/temperature" on page load
2. WHEN a Temperature_Reading is received via WebSocket, THE Dashboard SHALL update the displayed temperature value within 100 milliseconds
3. THE Dashboard SHALL display the temperature value rounded to 1 decimal place with unit symbol (°C)
4. THE Dashboard SHALL display the timestamp of the latest Temperature_Reading in human-readable format
5. WHEN the WebSocket connection is lost, THE Dashboard SHALL display a connection status indicator showing "disconnected"
6. WHEN the WebSocket connection is lost, THE Dashboard SHALL attempt reconnection every 3 seconds

### Requirement 11: Historical Temperature Graph

**User Story:** As a dashboard user, I want to view temperature trends over time, so that I can analyze historical patterns.

#### Acceptance Criteria

1. THE Dashboard SHALL display a line graph of Temperature_Readings using Recharts library
2. THE Dashboard SHALL provide time window selection buttons: "5 min", "15 min", "1 hour", "24 hours"
3. WHEN a time window button is clicked, THE Dashboard SHALL fetch Temperature_Readings from "/api/readings/history" for the selected duration
4. THE Dashboard SHALL plot temperature values on the Y-axis and timestamps on the X-axis
5. THE Dashboard SHALL display a horizontal threshold line on the graph at the configured Threshold value
6. THE Dashboard SHALL update the graph with new Temperature_Readings received via WebSocket
7. THE Dashboard SHALL display up to 500 data points on the graph; if more data points exist, THE Dashboard SHALL downsample the data

### Requirement 12: Alert Notifications Display

**User Story:** As a dashboard user, I want to see active and historical alerts, so that I am aware of threshold violations.

#### Acceptance Criteria

1. THE Dashboard SHALL display an alerts panel showing Alert_Events
2. THE Dashboard SHALL fetch Alert_Events from "/api/alerts" on page load
3. WHEN an Alert_Event is received via WebSocket, THE Dashboard SHALL add the alert to the alerts panel within 100 milliseconds
4. THE Dashboard SHALL display for each Alert_Event: device_id, temperature, threshold, alert_type, timestamp, and resolved status
5. THE Dashboard SHALL visually distinguish unresolved alerts (red indicator) from resolved alerts (green indicator)
6. THE Dashboard SHALL display the count of unresolved alerts prominently in a KPI card

### Requirement 13: System Status Indicators

**User Story:** As a dashboard user, I want to see system component health, so that I can verify all services are operational.

#### Acceptance Criteria

1. THE Dashboard SHALL display connection status indicators for: Backend_Service, MQTT_Broker, and Sensor_Simulator
2. THE Dashboard SHALL poll "/api/status" every 5 seconds to update status indicators
3. THE Dashboard SHALL display a green indicator when a component is connected/online
4. THE Dashboard SHALL display a red indicator when a component is disconnected/offline
5. THE Dashboard SHALL display Backend_Service uptime in the system information section

### Requirement 14: Threshold Configuration Control

**User Story:** As a dashboard user, I want to adjust the temperature threshold, so that I can customize alert sensitivity.

#### Acceptance Criteria

1. THE Dashboard SHALL display a threshold configuration input field showing the current Threshold value
2. THE Dashboard SHALL fetch the current Threshold from "/api/config" on page load
3. WHEN the user submits a new Threshold value, THE Dashboard SHALL send a PUT request to "/api/config" with the new value
4. IF the Backend_Service returns HTTP status 200, THE Dashboard SHALL update the displayed Threshold and show a success message
5. IF the Backend_Service returns an error status, THE Dashboard SHALL display the error message and revert the input field to the previous value
6. THE Dashboard SHALL validate that Threshold input is a number between 0 and 100 before submitting

### Requirement 15: Simulator Control Interface

**User Story:** As a dashboard user, I want to control the simulator from the web interface, so that I can start, stop, and test the system conveniently.

#### Acceptance Criteria

1. THE Dashboard SHALL display simulator control buttons: "Start Simulator", "Stop Simulator", "Test Spike"
2. WHEN the "Start Simulator" button is clicked, THE Dashboard SHALL send a POST request to "/api/simulator/start"
3. WHEN the "Stop Simulator" button is clicked, THE Dashboard SHALL send a POST request to "/api/simulator/stop"
4. WHEN the "Test Spike" button is clicked, THE Dashboard SHALL send a POST request to "/api/simulator/test-spike"
5. THE Dashboard SHALL disable the "Start Simulator" button when the Sensor_Simulator status is "online"
6. THE Dashboard SHALL disable the "Stop Simulator" and "Test Spike" buttons when the Sensor_Simulator status is "offline"
7. WHEN a control API call fails, THE Dashboard SHALL display an error message to the user

### Requirement 16: Key Performance Indicators Display

**User Story:** As a dashboard user, I want to see summary statistics, so that I can quickly assess system performance.

#### Acceptance Criteria

1. THE Dashboard SHALL display KPI cards showing: Current Temperature, Average Temperature, Maximum Temperature, Alert Count
2. THE Dashboard SHALL calculate Average Temperature from Temperature_Readings in the selected time window
3. THE Dashboard SHALL calculate Maximum Temperature from Temperature_Readings in the selected time window
4. THE Dashboard SHALL display Alert Count as the number of unresolved Alert_Events
5. THE Dashboard SHALL update KPI values when new Temperature_Readings are received via WebSocket

### Requirement 17: Recent Readings Table

**User Story:** As a dashboard user, I want to see a list of recent temperature readings, so that I can review detailed measurement history.

#### Acceptance Criteria

1. THE Dashboard SHALL display a table showing the 10 most recent Temperature_Readings
2. THE Dashboard SHALL display for each Temperature_Reading: timestamp, device_id, temperature, and unit
3. WHEN a new Temperature_Reading is received via WebSocket, THE Dashboard SHALL add it to the top of the table
4. IF the table contains more than 10 entries, THE Dashboard SHALL remove the oldest entry

### Requirement 18: Responsive Layout Design

**User Story:** As a dashboard user, I want the interface to work on different screen sizes, so that I can monitor the system on various devices.

#### Acceptance Criteria

1. THE Dashboard SHALL use a responsive CSS grid layout that adapts to screen widths from 320px to 2560px
2. WHEN the viewport width is below 768px, THE Dashboard SHALL stack cards vertically in a single column
3. WHEN the viewport width is 768px or above, THE Dashboard SHALL display cards in a multi-column grid layout
4. THE Dashboard SHALL ensure all interactive elements have a minimum touch target size of 44x44 pixels
5. THE Dashboard SHALL maintain readability of text at font sizes between 14px and 18px

### Requirement 19: Professional Visual Design

**User Story:** As a dashboard user, I want a modern and professional interface, so that the system appears credible and easy to use.

#### Acceptance Criteria

1. THE Dashboard SHALL use a dark color scheme with navy/charcoal background colors
2. THE Dashboard SHALL use CSS variables for consistent theming (colors, spacing, border-radius, shadows)
3. THE Dashboard SHALL display cards with subtle shadows and rounded corners (border-radius: 8-12px)
4. THE Dashboard SHALL use a sans-serif font family (system-ui, -apple-system, or Arial)
5. THE Dashboard SHALL use accent colors: green for normal status, yellow for warnings, red for alerts
6. THE Dashboard SHALL use Lucide React icons for visual indicators and controls

### Requirement 20: Error Handling and Recovery

**User Story:** As a system operator, I want graceful error handling, so that temporary failures do not cause system crashes.

#### Acceptance Criteria

1. WHEN the Backend_Service receives an invalid MQTT message, THE Backend_Service SHALL log the error, discard the message, and continue processing subsequent messages
2. WHEN the Database connection fails, THE Backend_Service SHALL return HTTP status 503 for API requests and log the error
3. WHEN the Dashboard cannot connect to the Backend_Service WebSocket, THE Dashboard SHALL display an error message and retry connection every 3 seconds
4. WHEN the Dashboard fetch request to an API endpoint fails, THE Dashboard SHALL display an error message and provide a retry option
5. WHEN the Sensor_Simulator cannot connect to the MQTT_Broker, THE Sensor_Simulator SHALL retry connection and log each attempt
6. IF the Backend_Service cannot start the Sensor_Simulator process, THE Backend_Service SHALL return an error response with diagnostic information

### Requirement 21: Graceful Shutdown Handling

**User Story:** As a system operator, I want components to shut down cleanly, so that no data is lost and resources are properly released.

#### Acceptance Criteria

1. WHEN the Backend_Service receives a termination signal (SIGINT or SIGTERM), THE Backend_Service SHALL close all WebSocket connections within 2 seconds
2. WHEN the Backend_Service receives a termination signal, THE Backend_Service SHALL disconnect from the MQTT_Broker gracefully
3. WHEN the Backend_Service receives a termination signal, THE Backend_Service SHALL close the Database connection
4. WHEN the Sensor_Simulator receives a termination signal, THE Sensor_Simulator SHALL publish a status message with "offline" status before disconnecting
5. THE Backend_Service SHALL complete processing of in-flight MQTT messages before shutting down

### Requirement 22: Configuration Management

**User Story:** As a system operator, I want centralized configuration, so that I can easily adjust system parameters.

#### Acceptance Criteria

1. THE Backend_Service SHALL read configuration from a JSON file named "config.json" on startup
2. THE config.json file SHALL contain fields: mqtt_broker_host, mqtt_broker_port, default_threshold, database_path, websocket_port
3. IF the config.json file does not exist, THE Backend_Service SHALL create it with default values
4. THE Backend_Service SHALL validate configuration values on startup and log warnings for invalid entries
5. THE Sensor_Simulator SHALL read configuration from a section in config.json containing: device_id, publish_interval, temperature_min, temperature_max

### Requirement 23: Logging and Observability

**User Story:** As a system operator, I want comprehensive logging, so that I can diagnose issues and monitor system behavior.

#### Acceptance Criteria

1. THE Backend_Service SHALL log all MQTT connection events (connected, disconnected, reconnecting) at INFO level
2. THE Backend_Service SHALL log all incoming MQTT messages at DEBUG level
3. THE Backend_Service SHALL log all Alert_Events at WARNING level
4. THE Backend_Service SHALL log all HTTP API requests with method, path, status code, and response time at INFO level
5. THE Sensor_Simulator SHALL log publishing events (successful/failed) at INFO level
6. THE Backend_Service SHALL log errors with stack traces at ERROR level
7. THE Backend_Service SHALL write logs to both console and a rotating log file (max 10MB per file, keep 5 files)

### Requirement 24: Setup Documentation

**User Story:** As a new user, I want clear setup instructions, so that I can run the system on my Windows laptop.

#### Acceptance Criteria

1. THE system SHALL include a README.md file with step-by-step setup instructions for Windows PowerShell
2. THE README.md SHALL document prerequisites: Python 3.11+, Node.js 18+, Eclipse Mosquitto
3. THE README.md SHALL provide commands for: installing dependencies, starting the MQTT broker, starting the backend, starting the simulator, starting the frontend
4. THE README.md SHALL document the complete directory structure with descriptions of each folder
5. THE README.md SHALL include a troubleshooting section covering common issues: MQTT connection failures, port conflicts, missing dependencies
6. THE README.md SHALL include a technology stack overview listing all frameworks and libraries used

### Requirement 25: Data Validation and Sanitization

**User Story:** As a backend service, I want to validate all inputs, so that invalid data does not corrupt the system.

#### Acceptance Criteria

1. THE Backend_Service SHALL validate that temperature values are numeric and within range -50.0 to 150.0
2. THE Backend_Service SHALL validate that device_id is a non-empty string with maximum length 100 characters
3. THE Backend_Service SHALL validate that unit is one of: "C", "F", "K"
4. THE Backend_Service SHALL validate that timestamp is a valid ISO 8601 formatted string
5. THE Backend_Service SHALL validate that Threshold configuration values are numeric and within range 0.0 to 100.0
6. IF validation fails for any field, THEN THE Backend_Service SHALL return HTTP status 400 with a descriptive error message

