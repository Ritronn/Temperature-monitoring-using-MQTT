import { useState, useEffect, useCallback } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { fetchReadingsHistory } from '../utils/api';
import { BarChart2, RefreshCw } from 'lucide-react';

const TIME_WINDOWS = [
  { label: '1 min', ms: 1 * 60 * 1000 },
  { label: '5 min', ms: 5 * 60 * 1000 },
  { label: '15 min', ms: 15 * 60 * 1000 },
  { label: '1 hour', ms: 60 * 60 * 1000 },
  { label: '24 hours', ms: 24 * 60 * 60 * 1000 },
];

const MAX_CHART_POINTS = 500;

/**
 * Downsample array to at most targetPoints using simple modulo-based method.
 */
function downsample(data, targetPoints) {
  if (data.length <= targetPoints) return data;
  const step = Math.ceil(data.length / targetPoints);
  return data.filter((_, idx) => idx % step === 0);
}

/**
 * Format ISO timestamp for chart axis labels.
 */
function formatAxisTime(isoString) {
  try {
    return new Date(isoString).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return isoString;
  }
}

/**
 * TemperatureChart - historical temperature graph with time window selection.
 *
 * @param {Object} currentReading - Latest reading to append to chart in real-time
 * @param {number} threshold - Current alert threshold value
 */
export default function TemperatureChart({ currentReading, threshold }) {
  const [selectedWindow, setSelectedWindow] = useState(0); // index into TIME_WINDOWS (0 = 1 min)
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadHistoricalData = useCallback(async () => {
    setLoading(true);
    setError(null);
    const endTime = new Date();
    const startTime = new Date(endTime.getTime() - TIME_WINDOWS[selectedWindow].ms);

    try {
      const result = await fetchReadingsHistory(
        startTime.toISOString(),
        endTime.toISOString()
      );
      let data = (result.readings || []).map((r) => ({
        timestamp: r.timestamp,
        label: formatAxisTime(r.timestamp),
        temperature: r.temperature,
      }));

      if (data.length > MAX_CHART_POINTS) {
        data = downsample(data, MAX_CHART_POINTS);
      }
      setChartData(data);
    } catch (err) {
      console.error('Failed to load chart history:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [selectedWindow]);

  // Load historical data when time window changes
  useEffect(() => {
    loadHistoricalData();
  }, [loadHistoricalData]);

  // Append live readings from WebSocket
  useEffect(() => {
    if (!currentReading) return;
    setChartData((prev) => {
      const next = [
        ...prev,
        {
          timestamp: currentReading.timestamp,
          label: formatAxisTime(currentReading.timestamp),
          temperature: currentReading.temperature,
        },
      ];
      return next.length > MAX_CHART_POINTS ? downsample(next, MAX_CHART_POINTS) : next;
    });
  }, [currentReading]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const temp = payload[0].value;
      const isHot = temp > threshold;
      return (
        <div className="chart-tooltip">
          <p className="tooltip-time">{label}</p>
          <p className="tooltip-temp" style={{ color: isHot ? '#dc2626' : '#2563eb' }}>
            {temp.toFixed(1)}°C
            {isHot && <span className="tooltip-alert"> ⚠ ALERT</span>}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <>
      <div className="chart-card card">
        <div className="chart-header">
          <h2 className="card-title">
            <BarChart2 size={18} color="#2563eb" style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle' }} />
            Temperature History
          </h2>
          <div className="chart-controls">
            <div className="time-buttons">
              {TIME_WINDOWS.map((w, idx) => (
                <button
                  key={w.label}
                  id={`time-window-${idx}`}
                  className={`time-btn ${selectedWindow === idx ? 'active' : ''}`}
                  onClick={() => setSelectedWindow(idx)}
                >
                  {w.label}
                </button>
              ))}
            </div>
            <button
              id="chart-refresh"
              className="button button-sm chart-refresh-btn"
              onClick={loadHistoricalData}
              disabled={loading}
              title="Refresh historical data"
            >
              <RefreshCw size={13} className={loading ? 'spin' : ''} />
            </button>
          </div>
        </div>

        {error && (
          <div className="alert alert-danger" style={{ marginBottom: 'var(--spacing-md)' }}>
            <span>{error}</span>
            <button className="button button-sm" onClick={loadHistoricalData}>
              Retry
            </button>
          </div>
        )}

        <div className="chart-container">
          {loading && chartData.length === 0 ? (
            <div className="chart-loading">Loading historical data…</div>
          ) : chartData.length === 0 ? (
            <div className="chart-empty">No data in selected time range.</div>
          ) : (
            <ResponsiveContainer width="100%" height={290}>
              <LineChart data={chartData} margin={{ top: 12, right: 16, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                <XAxis
                  dataKey="label"
                  stroke="#cbd5e1"
                  tick={{ fill: '#64748b', fontSize: 11 }}
                  interval="preserveStartEnd"
                  tickLine={{ stroke: '#e2e8f0' }}
                />
                <YAxis
                  stroke="#cbd5e1"
                  tick={{ fill: '#64748b', fontSize: 11 }}
                  domain={['dataMin - 2', 'dataMax + 2']}
                  tickFormatter={(v) => `${v}°`}
                  tickLine={{ stroke: '#e2e8f0' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <ReferenceLine
                  y={threshold}
                  stroke="#dc2626"
                  strokeDasharray="5 3"
                  strokeWidth={1.5}
                  label={{
                    value: `Threshold ${threshold}°C`,
                    fill: '#dc2626',
                    fontSize: 11,
                    position: 'insideTopRight',
                    fontWeight: 600,
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="temperature"
                  stroke="#2563eb"
                  strokeWidth={2.5}
                  dot={false}
                  isAnimationActive={false}
                  activeDot={{ r: 5, fill: '#2563eb', stroke: '#ffffff', strokeWidth: 2 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="chart-footer">
          <span className="text-muted" style={{ fontSize: 'var(--font-size-xs)' }}>
            {chartData.length} readings charted · Real-time auto-updating
          </span>
        </div>
      </div>

      <style>{`
        .chart-card {
          padding: 1.5rem;
          background: #ffffff;
        }

        .chart-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: var(--spacing-md);
          flex-wrap: wrap;
          gap: var(--spacing-sm);
        }

        .chart-controls {
          display: flex;
          align-items: center;
          gap: var(--spacing-sm);
          flex-wrap: wrap;
        }

        .time-buttons {
          display: flex;
          gap: 4px;
          background: #f1f5f9;
          padding: 3px;
          border-radius: var(--radius-md);
          border: 1px solid var(--color-border);
        }

        .time-btn {
          background: transparent;
          color: var(--color-text-secondary);
          border: none;
          padding: 5px 12px;
          font-family: var(--font-family-base);
          font-size: var(--font-size-xs);
          font-weight: 500;
          border-radius: var(--radius-sm);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .time-btn:hover {
          color: var(--color-text-primary);
        }

        .time-btn.active {
          background: #ffffff;
          color: var(--color-accent-primary);
          font-weight: 600;
          box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
        }

        .chart-refresh-btn {
          border-radius: var(--radius-md);
        }

        .chart-container {
          min-height: 290px;
          position: relative;
        }

        .chart-loading,
        .chart-empty {
          display: flex;
          align-items: center;
          justify-content: center;
          height: 290px;
          color: var(--color-text-muted);
          font-size: var(--font-size-sm);
        }

        .chart-footer {
          margin-top: var(--spacing-sm);
          text-align: right;
        }

        .chart-tooltip {
          background: #ffffff;
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          padding: 8px 14px;
          box-shadow: var(--shadow-lg);
        }

        .tooltip-time {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          margin-bottom: 2px;
          font-weight: 500;
        }

        .tooltip-temp {
          font-family: var(--font-family-heading);
          font-size: 1.125rem;
          font-weight: 700;
          margin: 0;
        }

        .tooltip-alert {
          font-size: var(--font-size-xs);
          margin-left: 6px;
        }

        .spin {
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
}
