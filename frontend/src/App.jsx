import { useEffect, useState } from 'react';
import './App.css';

import { useWebSocket } from './hooks/useWebSocket';
import { fetchStatus } from './utils/api';

import Header from './components/Header';
import KPICards from './components/KPICards';
import LiveTemperature from './components/LiveTemperature';
import TemperatureChart from './components/TemperatureChart';
import AlertsPanel from './components/AlertsPanel';
import RecentReadings from './components/RecentReadings';
import SystemStatus from './components/SystemStatus';
import ThresholdConfig from './components/ThresholdConfig';
import SimulatorControls from './components/SimulatorControls';

const WS_URL = 'ws://localhost:8000/ws/temperature';
const MAX_READINGS = 10;
const STATUS_POLL_MS = 5000;

/**
 * App - Root component for the ThermosenseIoT Dashboard.
 *
 * Manages global state derived from WebSocket messages and polls system status
 * to determine sensor online state for simulator control.
 */
function App() {
  const { isConnected, lastMessage } = useWebSocket(WS_URL);

  const [currentReading, setCurrentReading] = useState(null);
  const [readings, setReadings] = useState([]); // last 10 for table
  const [chartReadings, setChartReadings] = useState([]); // last 500 for avg/max
  const [latestAlert, setLatestAlert] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [threshold, setThreshold] = useState(35.0);
  const [sensorOnline, setSensorOnline] = useState(false);

  // Process incoming WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;

    if (lastMessage.type === 'temperature') {
      const reading = lastMessage.data;
      setCurrentReading(reading);

      // Update last-10 readings table
      setReadings((prev) => [reading, ...prev].slice(0, MAX_READINGS));

      // Update chart data (500-point buffer for KPI calculations)
      setChartReadings((prev) => [reading, ...prev].slice(0, 500));
    } else if (lastMessage.type === 'alert') {
      const alert = lastMessage.data;
      setLatestAlert(alert);
      setAlerts((prev) => [alert, ...prev]);
    }
  }, [lastMessage]);

  // Fetch initial latest readings and status on mount
  useEffect(() => {
    const initData = async () => {
      try {
        const { fetchLatestReadings, fetchAlerts } = await import('./utils/api');
        const [readingsRes, alertsRes] = await Promise.allSettled([
          fetchLatestReadings(),
          fetchAlerts(),
        ]);
        if (readingsRes.status === 'fulfilled' && readingsRes.value.readings?.length > 0) {
          const latest = readingsRes.value.readings[0];
          setCurrentReading(latest);
          setReadings(readingsRes.value.readings.slice(0, MAX_READINGS));
          setChartReadings(readingsRes.value.readings.slice(0, 500));
        }
        if (alertsRes.status === 'fulfilled' && alertsRes.value.alerts) {
          setAlerts(alertsRes.value.alerts);
          if (alertsRes.value.alerts.length > 0) {
            setLatestAlert(alertsRes.value.alerts[0]);
          }
        }
      } catch (e) {
        // silently fallback
      }
    };
    initData();

    const pollStatus = async () => {
      try {
        const data = await fetchStatus();
        setSensorOnline(data.sensor_online ?? false);
      } catch {
        // ignore - SystemStatus component handles error display
      }
    };
    pollStatus();
    const interval = setInterval(pollStatus, STATUS_POLL_MS);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="app-root">
      <Header isConnected={isConnected} />

      <main className="dashboard-main">
        {/* Connection warning banner */}
        {!isConnected && (
          <div className="connection-banner" role="alert">
            <span className="banner-icon">⚠</span>
            <span>WebSocket disconnected — attempting reconnection automatically…</span>
          </div>
        )}

        {/* KPI strip */}
        <section className="section" aria-label="Key performance indicators">
          <KPICards
            currentReading={currentReading}
            readings={chartReadings}
            alerts={alerts}
          />
        </section>

        {/* Main dashboard grid */}
        <div className="dashboard-grid">
          {/* Full-width chart */}
          <div className="grid-full">
            <TemperatureChart currentReading={currentReading} threshold={threshold} />
          </div>

          {/* Live temperature + alerts side by side */}
          <div className="grid-col">
            <LiveTemperature currentReading={currentReading} threshold={threshold} />
          </div>
          <div className="grid-col">
            <AlertsPanel latestAlert={latestAlert} />
          </div>

          {/* Recent readings table + system status controls */}
          <div className="grid-col">
            <RecentReadings readings={readings} />
          </div>
          <div className="grid-col grid-right">
            <SystemStatus />
            <ThresholdConfig onThresholdChange={setThreshold} />
            <SimulatorControls sensorOnline={sensorOnline} />
          </div>
        </div>
      </main>

      <style>{`
        .app-root {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          background-color: var(--color-bg-primary);
        }

        .dashboard-main {
          flex: 1;
          padding: 1.75rem 2rem;
          max-width: 1600px;
          margin: 0 auto;
          width: 100%;
        }

        .connection-banner {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          background: #fef2f2;
          border: 1px solid #fecaca;
          color: #dc2626;
          padding: 10px 16px;
          border-radius: var(--radius-md);
          margin-bottom: var(--spacing-lg);
          font-size: var(--font-size-sm);
          font-weight: 500;
          box-shadow: var(--shadow-xs);
          animation: gentlePulse 2s ease-in-out infinite;
        }

        @keyframes gentlePulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.75; }
        }

        .section {
          margin-bottom: var(--spacing-lg);
        }

        /* Dashboard grid layout */
        .dashboard-grid {
          display: grid;
          gap: var(--spacing-lg);
          grid-template-columns: 1fr;
          grid-template-areas:
            "full"
            "col1"
            "col2"
            "col3"
            "right";
        }

        .grid-full { grid-area: full; }
        .grid-col:nth-child(2) { grid-area: col1; }
        .grid-col:nth-child(3) { grid-area: col2; }
        .grid-col:nth-child(4) { grid-area: col3; }
        .grid-right { grid-area: right; }

        /* Tablet: 2 columns */
        @media (min-width: 768px) {
          .dashboard-grid {
            grid-template-columns: repeat(2, 1fr);
            grid-template-areas:
              "full full"
              "col1 col2"
              "col3 right";
          }
        }

        /* Desktop: 3 columns */
        @media (min-width: 1200px) {
          .dashboard-grid {
            grid-template-columns: repeat(3, 1fr);
            grid-template-areas:
              "full full full"
              "col1 col2 col3"
              "right right right";
          }

          .grid-right {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: var(--spacing-lg);
            grid-column: 1 / -1;
          }
        }

        /* Right column panel stacking on smaller screens */
        .grid-col.grid-right {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-lg);
        }

        @media (min-width: 1200px) {
          .grid-col.grid-right {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
          }
        }
      `}</style>
    </div>
  );
}

export default App;
