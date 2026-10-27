import { Thermometer, Clock } from 'lucide-react';

/**
 * LiveTemperature component - displays the most recent temperature reading.
 *
 * @param {Object} currentReading - Most recent temperature reading object
 * @param {number} threshold - Current alert threshold
 */
export default function LiveTemperature({ currentReading, threshold }) {
  const temp = currentReading ? currentReading.temperature : null;
  const unit = currentReading ? currentReading.unit : 'C';
  const isAlert = temp !== null && temp > threshold;

  const formatTimestamp = (ts) => {
    if (!ts) return '—';
    try {
      return new Date(ts).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return ts;
    }
  };

  const getColorClass = () => {
    if (temp === null) return '#94a3b8';
    if (isAlert) return '#dc2626';
    if (temp > threshold - 5) return '#d97706';
    return '#16a34a';
  };

  const tempColor = getColorClass();

  return (
    <>
      <div className="live-temp-card card">
        <div className="card-header">
          <h2 className="card-title">
            <Thermometer size={18} color="#2563eb" style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle' }} />
            Live Temperature
          </h2>
        </div>

        <div className="live-temp-display">
          <div
            className={`temp-value-large ${isAlert ? 'temp-alert-pulse' : ''}`}
            style={{ color: tempColor }}
            id="live-temp-value"
          >
            {temp !== null ? `${temp.toFixed(1)}°${unit}` : '—'}
          </div>

          {isAlert && (
            <div className="temp-alert-badge">
              ⚠ ABOVE THRESHOLD ({threshold.toFixed(1)}°{unit})
            </div>
          )}
        </div>

        <div className="live-temp-meta">
          <span className="meta-item">
            <Clock size={13} />
            {formatTimestamp(currentReading?.timestamp)}
          </span>
          {currentReading?.device_id && (
            <span className="meta-item device-id">
              {currentReading.device_id}
            </span>
          )}
        </div>

        {/* Threshold gauge bar */}
        {temp !== null && (
          <div className="threshold-bar-wrapper">
            <div className="threshold-bar-track">
              <div
                className="threshold-bar-fill"
                style={{
                  width: `${Math.min(100, (temp / Math.max(threshold * 1.5, 50)) * 100)}%`,
                  background: isAlert
                    ? 'linear-gradient(90deg, #d97706, #dc2626)'
                    : 'linear-gradient(90deg, #16a34a, #2563eb)',
                }}
              />
              <div
                className="threshold-marker"
                style={{
                  left: `${Math.min(100, (threshold / Math.max(threshold * 1.5, 50)) * 100)}%`,
                }}
                title={`Threshold: ${threshold}°C`}
              />
            </div>
            <div className="threshold-bar-labels">
              <span>0°C</span>
              <span style={{ color: '#dc2626', fontWeight: 600 }}>Threshold: {threshold.toFixed(1)}°C</span>
            </div>
          </div>
        )}
      </div>

      <style>{`
        .live-temp-card {
          min-height: 240px;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          background: #ffffff;
        }

        .live-temp-display {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 1rem 0 0.75rem;
          gap: var(--spacing-sm);
        }

        .temp-value-large {
          font-family: var(--font-family-heading);
          font-size: clamp(2.8rem, 6vw, 4.2rem);
          font-weight: 800;
          line-height: 1;
          letter-spacing: -0.03em;
          font-variant-numeric: tabular-nums;
          transition: color var(--transition-base);
        }

        .temp-alert-pulse {
          animation: tempPulse 1.5s ease-in-out infinite;
        }

        @keyframes tempPulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.88; transform: scale(1.02); }
        }

        .temp-alert-badge {
          background: #fef2f2;
          color: #dc2626;
          border: 1px solid #fecaca;
          border-radius: var(--radius-full);
          padding: 4px 12px;
          font-size: var(--font-size-xs);
          font-weight: 600;
          letter-spacing: 0.04em;
          box-shadow: 0 1px 2px rgba(220, 38, 38, 0.08);
          animation: blink 1s ease-in-out infinite;
        }

        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }

        .live-temp-meta {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: var(--spacing-sm);
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          flex-wrap: wrap;
          padding-top: var(--spacing-sm);
        }

        .meta-item {
          display: inline-flex;
          align-items: center;
          gap: 5px;
        }

        .device-id {
          font-family: monospace;
          background: #f1f5f9;
          border: 1px solid var(--color-border);
          color: var(--color-text-secondary);
          padding: 2px 8px;
          border-radius: var(--radius-sm);
          font-weight: 500;
        }

        .threshold-bar-wrapper {
          margin-top: var(--spacing-md);
        }

        .threshold-bar-track {
          position: relative;
          width: 100%;
          height: 7px;
          background: #f1f5f9;
          border: 1px solid var(--color-border);
          border-radius: var(--radius-full);
          overflow: visible;
        }

        .threshold-bar-fill {
          height: 100%;
          border-radius: var(--radius-full);
          transition: width 0.4s ease;
        }

        .threshold-marker {
          position: absolute;
          top: -4px;
          transform: translateX(-50%);
          width: 3px;
          height: 15px;
          background: #dc2626;
          border-radius: 2px;
          box-shadow: 0 0 2px rgba(220, 38, 38, 0.5);
        }

        .threshold-bar-labels {
          display: flex;
          justify-content: space-between;
          margin-top: 6px;
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
        }
      `}</style>
    </>
  );
}
