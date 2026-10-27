/**
 * API client utilities for ThermosenseIoT Dashboard
 * Provides functions to interact with the FastAPI backend service
 */

// API base URL - backend service running on localhost:8000
const API_BASE_URL = 'http://localhost:8000';

/**
 * Helper function to handle HTTP errors
 * @param {Response} response - Fetch API response object
 * @throws {Error} - Throws error with descriptive message
 */
async function handleResponse(response) {
  if (!response.ok) {
    let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
    
    // Try to extract error details from response body
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = `${errorMessage} - ${errorData.detail}`;
      }
    } catch (e) {
      // If response body is not JSON, use status text
    }
    
    throw new Error(errorMessage);
  }
  
  return response.json();
}

/**
 * Health check endpoint
 * GET /api/health
 * @returns {Promise<Object>} - { status: "healthy" }
 */
export async function fetchHealth() {
  const response = await fetch(`${API_BASE_URL}/api/health`);
  return handleResponse(response);
}

/**
 * System status endpoint
 * GET /api/status
 * @returns {Promise<Object>} - { mqtt_connected, sensor_online, backend_uptime_seconds }
 */
export async function fetchStatus() {
  const response = await fetch(`${API_BASE_URL}/api/status`);
  return handleResponse(response);
}

/**
 * Latest readings endpoint
 * GET /api/readings/latest
 * @returns {Promise<Object>} - { readings: [...] }
 */
export async function fetchLatestReadings() {
  const response = await fetch(`${API_BASE_URL}/api/readings/latest`);
  return handleResponse(response);
}

/**
 * Historical readings endpoint
 * GET /api/readings/history
 * @param {string} startTime - ISO 8601 timestamp (start of time range)
 * @param {string} endTime - ISO 8601 timestamp (end of time range)
 * @param {string} [deviceId] - Optional device ID filter
 * @returns {Promise<Object>} - { readings: [...] }
 */
export async function fetchReadingsHistory(startTime, endTime, deviceId = null) {
  let url = `${API_BASE_URL}/api/readings/history?start_time=${encodeURIComponent(startTime)}&end_time=${encodeURIComponent(endTime)}`;
  
  if (deviceId) {
    url += `&device_id=${encodeURIComponent(deviceId)}`;
  }
  
  const response = await fetch(url);
  return handleResponse(response);
}

/**
 * Alerts endpoint
 * GET /api/alerts
 * @param {boolean} [resolved] - Optional filter for resolved status (true/false)
 * @returns {Promise<Object>} - { alerts: [...] }
 */
export async function fetchAlerts(resolved = null) {
  let url = `${API_BASE_URL}/api/alerts`;
  
  if (resolved !== null) {
    url += `?resolved=${resolved}`;
  }
  
  const response = await fetch(url);
  return handleResponse(response);
}

/**
 * Get configuration endpoint
 * GET /api/config
 * @returns {Promise<Object>} - { threshold: number }
 */
export async function fetchConfig() {
  const response = await fetch(`${API_BASE_URL}/api/config`);
  return handleResponse(response);
}

/**
 * Update configuration endpoint
 * PUT /api/config
 * @param {number} threshold - New threshold value (0-100)
 * @returns {Promise<Object>} - { threshold: number }
 */
export async function updateConfig(threshold) {
  const response = await fetch(`${API_BASE_URL}/api/config`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ threshold }),
  });
  return handleResponse(response);
}

/**
 * Start simulator endpoint
 * POST /api/simulator/start
 * @returns {Promise<Object>} - { message: string }
 */
export async function startSimulator() {
  const response = await fetch(`${API_BASE_URL}/api/simulator/start`, {
    method: 'POST',
  });
  return handleResponse(response);
}

/**
 * Stop simulator endpoint
 * POST /api/simulator/stop
 * @returns {Promise<Object>} - { message: string }
 */
export async function stopSimulator() {
  const response = await fetch(`${API_BASE_URL}/api/simulator/stop`, {
    method: 'POST',
  });
  return handleResponse(response);
}

/**
 * Test spike endpoint
 * POST /api/simulator/test-spike
 * @returns {Promise<Object>} - { message: string }
 */
export async function testSpike() {
  const response = await fetch(`${API_BASE_URL}/api/simulator/test-spike`, {
    method: 'POST',
  });
  return handleResponse(response);
}
