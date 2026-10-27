import { Table } from 'lucide-react';

/**
 * RecentReadings - table of the 10 most recent temperature readings.
 *
 * @param {Array} readings - Array of the most recent temperature readings
 */
export default function RecentReadings({ readings }) {
  const formatTimestamp = (ts) => {
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

  return (
    <>
      <div className="readings-card card">
        <div className="card-header">
          <h2 className="card-title">
            <Table size={18} color="#2563eb" style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle' }} />
            Recent Readings
            <span className="readings-count">{readings.length}/10</span>
          </h2>
        </div>

        {readings.length === 0 ? (
          <div className="readings-empty">No readings yet. Waiting for telemetry data…</div>
        ) : (
          <div className="table-wrapper">
            <table className="table readings-table" id="recent-readings-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Device</th>
                  <th>Temperature</th>
                  <th>Unit</th>
                </tr>
              </thead>
              <tbody>
                {readings.map((reading, idx) => (
                  <tr
                    key={`${reading.device_id}-${reading.timestamp}-${idx}`}
                    className={idx === 0 ? 'newest-row' : ''}
                  >
                    <td className="time-cell">{formatTimestamp(reading.timestamp)}</td>
                    <td>
                      <span className="device-tag">{reading.device_id}</span>
                    </td>
                    <td className="temp-cell">
                      {reading.temperature.toFixed(1)}°
                    </td>
                    <td>
                      <span className="unit-tag">°{reading.unit}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <style>{`
        .readings-card {
          background: #ffffff;
          overflow: hidden;
        }

        .readings-count {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          font-weight: 500;
          margin-left: var(--spacing-sm);
          background: #f1f5f9;
          padding: 2px 8px;
          border-radius: var(--radius-full);
          border: 1px solid var(--color-border);
        }

        .readings-empty {
          text-align: center;
          padding: var(--spacing-xl);
          color: var(--color-text-muted);
          font-size: var(--font-size-sm);
        }

        .table-wrapper {
          overflow-x: auto;
        }

        .readings-table {
          min-width: 320px;
        }

        .newest-row td {
          background: #eff6ff !important;
          animation: highlightRow 0.8s ease;
        }

        @keyframes highlightRow {
          from { background: #dbeafe !important; }
          to { background: #eff6ff !important; }
        }

        .time-cell {
          font-variant-numeric: tabular-nums;
          font-family: monospace;
          font-size: var(--font-size-xs) !important;
          color: var(--color-text-muted) !important;
        }

        .device-tag {
          font-family: monospace;
          background: #f8fafc;
          border: 1px solid var(--color-border);
          padding: 2px 7px;
          border-radius: var(--radius-sm);
          font-size: var(--font-size-xs);
          color: var(--color-text-secondary);
          font-weight: 500;
        }

        .temp-cell {
          font-family: var(--font-family-heading);
          font-weight: 700 !important;
          color: #0f172a !important;
          font-variant-numeric: tabular-nums;
        }

        .unit-tag {
          background: #f0fdf4;
          color: #16a34a;
          border: 1px solid #bbf7d0;
          padding: 2px 7px;
          border-radius: var(--radius-sm);
          font-size: var(--font-size-xs);
          font-weight: 600;
        }
      `}</style>
    </>
  );
}
