import { useState } from 'react';
import { startSimulator, stopSimulator, testSpike } from '../utils/api';
import { Play, Square, Zap } from 'lucide-react';

/**
 * SimulatorControls - Start, Stop, and Test Spike buttons for the sensor simulator.
 *
 * @param {boolean} sensorOnline - Whether the sensor is currently online
 */
export default function SimulatorControls({ sensorOnline }) {
  const [loading, setLoading] = useState(null); // 'start' | 'stop' | 'spike' | null
  const [message, setMessage] = useState(null); // { type, text }

  const showMessage = (type, text) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 4000);
  };

  const handleStart = async () => {
    setLoading('start');
    try {
      const result = await startSimulator();
      showMessage('success', result.message || 'Simulator started successfully');
    } catch (err) {
      showMessage('error', err.message);
    } finally {
      setLoading(null);
    }
  };

  const handleStop = async () => {
    setLoading('stop');
    try {
      const result = await stopSimulator();
      showMessage('success', result.message || 'Simulator stopped');
    } catch (err) {
      showMessage('error', err.message);
    } finally {
      setLoading(null);
    }
  };

  const handleSpike = async () => {
    setLoading('spike');
    try {
      const result = await testSpike();
      showMessage('success', result.message || 'Spike signal sent');
    } catch (err) {
      showMessage('error', err.message);
    } finally {
      setLoading(null);
    }
  };

  const busy = loading !== null;

  return (
    <>
      <div className="simulator-card card">
        <div className="card-header">
          <h2 className="card-title">
            <Zap size={18} color="#2563eb" style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle' }} />
            Simulator Control
          </h2>
          <span
            className={`sim-status-badge ${sensorOnline ? 'sim-online' : 'sim-offline'}`}
          >
            <span className="sim-dot" />
            {sensorOnline ? 'Running' : 'Stopped'}
          </span>
        </div>

        {message && (
          <div
            className={`alert ${message.type === 'success' ? 'alert-success' : 'alert-danger'}`}
            style={{ marginBottom: 'var(--spacing-md)' }}
          >
            <span>{message.text}</span>
          </div>
        )}

        <div className="sim-buttons">
          <button
            id="sim-start"
            className="button button-success sim-btn"
            onClick={handleStart}
            disabled={busy || sensorOnline}
            title={sensorOnline ? 'Simulator already running' : 'Start the sensor simulator'}
          >
            {loading === 'start' ? (
              <span className="spinner" />
            ) : (
              <Play size={15} fill="currentColor" />
            )}
            Start
          </button>

          <button
            id="sim-stop"
            className="button button-danger sim-btn"
            onClick={handleStop}
            disabled={busy || !sensorOnline}
            title={!sensorOnline ? 'Simulator is not running' : 'Stop the sensor simulator'}
          >
            {loading === 'stop' ? (
              <span className="spinner" />
            ) : (
              <Square size={15} fill="currentColor" />
            )}
            Stop
          </button>

          <button
            id="sim-spike"
            className="button button-warning sim-btn"
            onClick={handleSpike}
            disabled={busy || !sensorOnline}
            title={!sensorOnline ? 'Simulator must be running' : 'Trigger a temperature spike above threshold'}
          >
            {loading === 'spike' ? (
              <span className="spinner" />
            ) : (
              <Zap size={15} />
            )}
            Spike
          </button>
        </div>

        <p className="sim-hint">
          Sensor publishes telemetry every 2 seconds. Use "Spike" to simulate an alert condition.
        </p>
      </div>

      <style>{`
        .simulator-card {
          background: #ffffff;
        }

        .simulator-card .card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: var(--spacing-sm);
        }

        .sim-status-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 3px 10px;
          border-radius: var(--radius-full);
          font-size: var(--font-size-xs);
          font-weight: 600;
        }

        .sim-online {
          background: #f0fdf4;
          color: #16a34a;
          border: 1px solid #bbf7d0;
        }

        .sim-offline {
          background: #fef2f2;
          color: #dc2626;
          border: 1px solid #fecaca;
        }

        .sim-dot {
          width: 7px;
          height: 7px;
          border-radius: 50%;
          background: currentColor;
        }

        .sim-online .sim-dot {
          animation: simPulse 1.5s ease-in-out infinite;
        }

        @keyframes simPulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.4; }
        }

        .sim-buttons {
          display: flex;
          flex-wrap: wrap;
          gap: var(--spacing-sm);
          margin-bottom: var(--spacing-md);
        }

        .sim-btn {
          flex: 1;
          min-width: 90px;
        }

        .sim-hint {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          margin: 0;
          line-height: 1.4;
        }

        .spinner {
          display: inline-block;
          width: 14px;
          height: 14px;
          border: 2px solid currentColor;
          border-top-color: transparent;
          border-radius: 50%;
          animation: spin 0.7s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
}
