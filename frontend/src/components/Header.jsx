import { Thermometer, Wifi, WifiOff } from 'lucide-react';

/**
 * Header component for ThermosenseIoT Dashboard.
 * Displays application title, branding, and WebSocket connection status.
 *
 * @param {boolean} isConnected - Whether the WebSocket is connected
 */
export default function Header({ isConnected }) {
  return (
    <header className="dashboard-header">
      <div className="header-brand">
        <div className="header-icon">
          <Thermometer size={26} color="#2563eb" />
        </div>
        <div className="header-titles">
          <h1 className="header-title">Thermosense<span className="title-accent">IoT</span></h1>
          <p className="header-subtitle">Real-time Temperature Monitoring & Telemetry</p>
        </div>
      </div>

      <div className="header-status">
        <span
          className={`ws-status ${isConnected ? 'ws-connected' : 'ws-disconnected'}`}
          title={isConnected ? 'Live data streaming' : 'Attempting to reconnect…'}
        >
          {isConnected ? <Wifi size={15} /> : <WifiOff size={15} />}
          <span>{isConnected ? 'System Live' : 'Reconnecting…'}</span>
        </span>
      </div>

      <style>{`
        .dashboard-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 1rem 2rem;
          background: rgba(255, 255, 255, 0.95);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border-bottom: 1px solid var(--color-border);
          box-shadow: 0 1px 3px 0 rgba(15, 23, 42, 0.04);
          position: sticky;
          top: 0;
          z-index: 50;
          flex-wrap: wrap;
          gap: var(--spacing-md);
        }

        .header-brand {
          display: flex;
          align-items: center;
          gap: var(--spacing-md);
        }

        .header-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 44px;
          height: 44px;
          background: #eff6ff;
          border-radius: var(--radius-md);
          border: 1px solid #bfdbfe;
          box-shadow: 0 1px 2px rgba(37, 99, 235, 0.08);
        }

        .header-title {
          font-family: var(--font-family-heading);
          font-size: 1.35rem;
          font-weight: 700;
          letter-spacing: -0.02em;
          margin: 0;
          color: #0f172a;
        }

        .title-accent {
          color: var(--color-accent-primary);
          margin-left: 1px;
        }

        .header-subtitle {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          font-weight: 500;
          margin: 0;
        }

        .ws-status {
          display: inline-flex;
          align-items: center;
          gap: 7px;
          padding: 6px 14px;
          border-radius: var(--radius-full);
          font-size: var(--font-size-xs);
          font-weight: 600;
          letter-spacing: 0.02em;
          transition: all var(--transition-base);
        }

        .ws-connected {
          background: #f0fdf4;
          color: #16a34a;
          border: 1px solid #bbf7d0;
          box-shadow: 0 1px 2px rgba(22, 163, 74, 0.08);
        }

        .ws-disconnected {
          background: #fef2f2;
          color: #dc2626;
          border: 1px solid #fecaca;
          box-shadow: 0 1px 2px rgba(220, 38, 38, 0.08);
          animation: blink 1.5s ease-in-out infinite;
        }

        @keyframes blink {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </header>
  );
}
