import { useEffect, useState } from 'react';
import { fetchStatus } from '../utils/api';
import { Server, Radio, Cpu, Clock } from 'lucide-react';

/**
 * Format uptime in seconds to human-readable string.
 */
function formatUptime(seconds) {
  if (seconds < 60) return `${seconds}s`;
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  return `${h}h ${m}m`;
}

/**
 * SystemStatus - displays connection indicators for Backend, MQTT, and Sensor.
 * Polls /api/status every 5 seconds.
 */
export default function SystemStatus() {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);

  const fetchSystemStatus = async () => {
    try {
      const data = await fetchStatus();
      setStatus(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    fetchSystemStatus();
    const interval = setInterval(fetchSystemStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const indicators = [
    {
      id: 'status-backend',
      label: 'FastAPI Backend',
      icon: <Server size={15} />,
      online: status !== null,
      detail: status ? `Uptime: ${formatUptime(status.backend_uptime_seconds)}` : 'Connecting…',
    },
    {
      id: 'status-mqtt',
      label: 'MQTT Broker',
      icon: <Radio size={15} />,
      online: status?.mqtt_connected ?? false,
      detail: status?.mqtt_connected ? 'Connected' : 'Disconnected',
    },
    {
      id: 'status-sensor',
      label: 'IoT Sensor Node',
      icon: <Cpu size={15} />,
      online: status?.sensor_online ?? false,
      detail: status?.sensor_online ? 'Publishing' : 'Offline',
    },
  ];

  return (
    <>
      <div className="system-status-card card">
        <div className="card-header">
          <h2 className="card-title">
            <Server size={18} color="#2563eb" style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle' }} />
            System Status
          </h2>
          {status && (
            <span className="uptime-badge">
              <Clock size={12} />
              Up {formatUptime(status.backend_uptime_seconds)}
            </span>
          )}
        </div>

        {error && (
          <div className="alert alert-warning" style={{ marginBottom: 'var(--spacing-md)' }}>
            <span>Backend unreachable: {error}</span>
          </div>
        )}

        <div className="status-grid">
          {indicators.map((item) => (
            <div key={item.id} id={item.id} className="status-item">
              <div
                className="status-icon-wrapper"
                style={{
                  color: item.online ? '#16a34a' : '#dc2626',
                  background: item.online ? '#f0fdf4' : '#fef2f2',
                  border: `1px solid ${item.online ? '#bbf7d0' : '#fecaca'}`,
                }}
              >
                {item.icon}
              </div>
              <div className="status-text">
                <span className="status-label">{item.label}</span>
                <span
                  className="status-detail"
                  style={{ color: item.online ? '#16a34a' : '#64748b' }}
                >
                  {item.detail}
                </span>
              </div>
              <div
                className={`status-dot ${item.online ? 'dot-online' : 'dot-offline'}`}
                title={item.online ? 'Online' : 'Offline'}
              />
            </div>
          ))}
        </div>
      </div>

      <style>{`
        .system-status-card {
          background: #ffffff;
        }

        .system-status-card .card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .uptime-badge {
          display: inline-flex;
          align-items: center;
          gap: 4px;
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          background: #f1f5f9;
          padding: 2px 8px;
          border-radius: var(--radius-full);
          border: 1px solid var(--color-border);
        }

        .status-grid {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .status-item {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);
          padding: 10px 14px;
          background: #f8fafc;
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          transition: background var(--transition-fast), border-color var(--transition-fast);
        }

        .status-item:hover {
          background: #f1f5f9;
          border-color: var(--color-border-strong);
        }

        .status-icon-wrapper {
          width: 34px;
          height: 34px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: var(--radius-md);
          flex-shrink: 0;
        }

        .status-text {
          flex: 1;
          display: flex;
          flex-direction: column;
          gap: 2px;
        }

        .status-label {
          font-size: var(--font-size-sm);
          font-weight: 600;
          color: var(--color-text-primary);
        }

        .status-detail {
          font-size: var(--font-size-xs);
          font-weight: 500;
          transition: color var(--transition-base);
        }

        .status-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .dot-online {
          background: #16a34a;
          box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.2);
          animation: pulse 2s ease-in-out infinite;
        }

        .dot-offline {
          background: #dc2626;
          box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.2);
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
      `}</style>
    </>
  );
}
