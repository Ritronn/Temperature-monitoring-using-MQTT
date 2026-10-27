import { Thermometer, TrendingUp, BarChart2, AlertTriangle } from 'lucide-react';

/**
 * KPI Cards component displaying key performance indicators.
 *
 * @param {Object} currentReading - Most recent temperature reading
 * @param {Array}  readings - Array of recent temperature readings
 * @param {Array}  alerts - Array of all alerts
 */
export default function KPICards({ currentReading, readings, alerts }) {
  const currentTemp = currentReading ? currentReading.temperature : null;
  const unit = currentReading ? currentReading.unit : 'C';

  const avgTemp =
    readings.length > 0
      ? readings.reduce((sum, r) => sum + r.temperature, 0) / readings.length
      : null;

  const maxTemp =
    readings.length > 0
      ? Math.max(...readings.map((r) => r.temperature))
      : null;

  const unresolvedAlerts = alerts.filter((a) => !a.resolved).length;

  const fmt = (val) =>
    val !== null && val !== undefined ? val.toFixed(1) : '—';

  const cards = [
    {
      id: 'kpi-current',
      label: 'Current Temp',
      value: currentTemp !== null ? `${fmt(currentTemp)}°${unit}` : '—',
      icon: <Thermometer size={20} />,
      color: '#2563eb',
      bg: '#eff6ff',
      border: '#bfdbfe',
    },
    {
      id: 'kpi-avg',
      label: 'Average Temp',
      value: avgTemp !== null ? `${fmt(avgTemp)}°${unit}` : '—',
      icon: <TrendingUp size={20} />,
      color: '#16a34a',
      bg: '#f0fdf4',
      border: '#bbf7d0',
    },
    {
      id: 'kpi-max',
      label: 'Peak Temp',
      value: maxTemp !== null ? `${fmt(maxTemp)}°${unit}` : '—',
      icon: <BarChart2 size={20} />,
      color: '#d97706',
      bg: '#fffbeb',
      border: '#fde68a',
    },
    {
      id: 'kpi-alerts',
      label: 'Active Alerts',
      value: unresolvedAlerts.toString(),
      icon: <AlertTriangle size={20} />,
      color: unresolvedAlerts > 0 ? '#dc2626' : '#16a34a',
      bg: unresolvedAlerts > 0 ? '#fef2f2' : '#f0fdf4',
      border: unresolvedAlerts > 0 ? '#fecaca' : '#bbf7d0',
    },
  ];

  return (
    <>
      <div className="kpi-grid">
        {cards.map((card) => (
          <div
            key={card.id}
            id={card.id}
            className="kpi-card"
          >
            <div
              className="kpi-icon"
              style={{ color: card.color, background: card.bg, borderColor: card.border }}
            >
              {card.icon}
            </div>
            <div className="kpi-content">
              <span className="kpi-label">{card.label}</span>
              <span className="kpi-value" style={{ color: card.color }}>
                {card.value}
              </span>
            </div>
          </div>
        ))}
      </div>

      <style>{`
        .kpi-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: var(--spacing-md);
        }

        @media (min-width: 768px) {
          .kpi-grid {
            grid-template-columns: repeat(4, 1fr);
          }
        }

        .kpi-card {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);
          padding: 1.15rem 1.25rem;
          background: #ffffff;
          border-radius: var(--radius-lg);
          border: 1px solid var(--color-border);
          box-shadow: var(--shadow-sm);
          transition: transform var(--transition-base), box-shadow var(--transition-base), border-color var(--transition-base);
        }

        .kpi-card:hover {
          transform: translateY(-2px);
          box-shadow: var(--shadow-md);
          border-color: var(--color-border-strong);
        }

        .kpi-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 44px;
          height: 44px;
          border-radius: var(--radius-md);
          border: 1px solid transparent;
          flex-shrink: 0;
        }

        .kpi-content {
          display: flex;
          flex-direction: column;
          gap: 2px;
          min-width: 0;
        }

        .kpi-label {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .kpi-value {
          font-family: var(--font-family-heading);
          font-size: 1.5rem;
          font-weight: 700;
          line-height: 1.1;
          letter-spacing: -0.02em;
          font-variant-numeric: tabular-nums;
        }
      `}</style>
    </>
  );
}
