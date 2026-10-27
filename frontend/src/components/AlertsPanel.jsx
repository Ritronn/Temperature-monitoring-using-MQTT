import { useEffect, useState } from 'react';
import { fetchAlerts } from '../utils/api';
import { Bell, CheckCircle, XCircle } from 'lucide-react';

/**
 * AlertsPanel - displays historical and live alert events.
 *
 * @param {Object} latestAlert - Most recent alert received via WebSocket
 */
export default function AlertsPanel({ latestAlert }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [showResolved, setShowResolved] = useState(true);

  const loadAlerts = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAlerts();
      setAlerts(result.alerts || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    loadAlerts();
  }, []);

  // Append new alerts from WebSocket
  useEffect(() => {
    if (!latestAlert) return;
    setAlerts((prev) => {
      // Avoid duplicates
      const exists = prev.some(
        (a) =>
          a.device_id === latestAlert.device_id &&
          a.timestamp === latestAlert.timestamp
      );
      if (exists) return prev;
      return [latestAlert, ...prev];
    });
  }, [latestAlert]);

  const displayed = showResolved
    ? alerts
    : alerts.filter((a) => !a.resolved);

  const unresolvedCount = alerts.filter((a) => !a.resolved).length;

  const formatTimestamp = (ts) => {
    try {
      return new Date(ts).toLocaleString([], {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return ts;
    }
  };

  return (
    <>
      <div className="alerts-card card">
        <div className="card-header alerts-header">
          <h2 className="card-title">
            <Bell size={18} color="#2563eb" style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle' }} />
            Alerts
            {unresolvedCount > 0 && (
              <span className="alert-badge">{unresolvedCount}</span>
            )}
          </h2>
          <div className="alerts-controls">
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={showResolved}
                onChange={(e) => setShowResolved(e.target.checked)}
                id="show-resolved-toggle"
              />
              <span>Show resolved</span>
            </label>
            <button
              id="alerts-refresh"
              className="button button-sm"
              onClick={loadAlerts}
              disabled={loading}
            >
              Refresh
            </button>
          </div>
        </div>

        {error && (
          <div className="alert alert-danger">
            <span>{error}</span>
            <button className="button button-sm" onClick={loadAlerts}>
              Retry
            </button>
          </div>
        )}

        {loading && alerts.length === 0 ? (
          <div className="alerts-empty">Loading alerts…</div>
        ) : displayed.length === 0 ? (
          <div className="alerts-empty">
            <CheckCircle size={32} color="#16a34a" />
            <p>No {showResolved ? '' : 'active '}alerts detected</p>
          </div>
        ) : (
          <div className="alerts-list">
            {displayed.map((alert, idx) => (
              <div
                key={`${alert.device_id}-${alert.timestamp}-${idx}`}
                className={`alert-item ${alert.resolved ? 'resolved' : 'active'}`}
              >
                <div className="alert-icon">
                  {alert.resolved ? (
                    <CheckCircle size={18} color="#16a34a" />
                  ) : (
                    <XCircle size={18} color="#dc2626" />
                  )}
                </div>
                <div className="alert-details">
                  <div className="alert-row-1">
                    <span className="alert-device">{alert.device_id}</span>
                    <span
                      className="alert-temp"
                      style={{ color: alert.resolved ? '#64748b' : '#dc2626' }}
                    >
                      {alert.temperature?.toFixed(1)}°C
                    </span>
                  </div>
                  <div className="alert-row-2">
                    <span className="alert-type">{alert.alert_type?.replace('_', ' ')}</span>
                    <span className="alert-threshold">
                      threshold: {alert.threshold?.toFixed(1)}°C
                    </span>
                    <span className="alert-time">
                      {formatTimestamp(alert.timestamp)}
                    </span>
                  </div>
                </div>
                <div className="alert-status-badge">
                  <span
                    className={`status-pill ${alert.resolved ? 'status-pill-resolved' : 'status-pill-active'}`}
                  >
                    {alert.resolved ? 'Resolved' : 'Active'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <style>{`
        .alerts-card {
          max-height: 420px;
          display: flex;
          flex-direction: column;
          background: #ffffff;
        }

        .alerts-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: var(--spacing-sm);
        }

        .alert-badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          min-width: 20px;
          height: 20px;
          padding: 0 6px;
          background: #dc2626;
          color: white;
          border-radius: var(--radius-full);
          font-size: var(--font-size-xs);
          font-weight: 700;
          margin-left: 8px;
          vertical-align: middle;
        }

        .alerts-controls {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
        }

        .toggle-label {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          cursor: pointer;
          user-select: none;
        }

        .toggle-label input {
          cursor: pointer;
          accent-color: var(--color-accent-primary);
        }

        .alerts-empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: var(--spacing-xl);
          color: var(--color-text-muted);
          gap: var(--spacing-sm);
          font-size: var(--font-size-sm);
        }

        .alerts-empty p {
          margin: 0;
          color: var(--color-text-muted);
        }

        .alerts-list {
          overflow-y: auto;
          max-height: 320px;
          display: flex;
          flex-direction: column;
          gap: 8px;
          padding-right: 4px;
        }

        .alerts-list::-webkit-scrollbar {
          width: 5px;
        }

        .alerts-list::-webkit-scrollbar-track {
          background: #f8fafc;
        }

        .alerts-list::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: var(--radius-full);
        }

        .alert-item {
          display: flex;
          align-items: flex-start;
          gap: var(--spacing-sm);
          padding: 10px 14px;
          border-radius: var(--radius-md);
          border: 1px solid var(--color-border);
          border-left-width: 4px;
          transition: background var(--transition-fast), transform var(--transition-fast);
        }

        .alert-item.active {
          background: #fef2f2;
          border-left-color: #dc2626;
        }

        .alert-item.resolved {
          background: #f8fafc;
          border-left-color: #16a34a;
          opacity: 0.9;
        }

        .alert-icon {
          flex-shrink: 0;
          margin-top: 1px;
        }

        .alert-details {
          flex: 1;
          min-width: 0;
        }

        .alert-row-1 {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 2px;
        }

        .alert-device {
          font-family: monospace;
          font-size: var(--font-size-xs);
          color: var(--color-text-primary);
          font-weight: 600;
        }

        .alert-temp {
          font-family: var(--font-family-heading);
          font-weight: 700;
          font-size: var(--font-size-sm);
        }

        .alert-row-2 {
          display: flex;
          gap: var(--spacing-sm);
          flex-wrap: wrap;
        }

        .alert-type {
          text-transform: capitalize;
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        .alert-threshold {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }

        .alert-time {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          margin-left: auto;
        }

        .alert-status-badge {
          flex-shrink: 0;
        }

        .status-pill {
          display: inline-flex;
          align-items: center;
          padding: 2px 8px;
          border-radius: var(--radius-full);
          font-size: 0.7rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .status-pill-active {
          background: #fee2e2;
          color: #991b1b;
        }

        .status-pill-resolved {
          background: #dcfce7;
          color: #166534;
        }
      `}</style>
    </>
  );
}
