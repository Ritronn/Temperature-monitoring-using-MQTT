import { useState, useEffect } from 'react';
import { fetchConfig, updateConfig } from '../utils/api';
import { Settings, Check, X } from 'lucide-react';

/**
 * ThresholdConfig - allows users to view and update the alert threshold.
 *
 * @param {function} onThresholdChange - Callback to notify parent of new threshold
 */
export default function ThresholdConfig({ onThresholdChange }) {
  const [threshold, setThreshold] = useState('');
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null); // { type: 'success'|'error', text }
  const [error, setError] = useState(null);

  const loadConfig = async () => {
    try {
      const data = await fetchConfig();
      setThreshold(data.threshold);
      setInputValue(String(data.threshold));
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage(null);

    const val = parseFloat(inputValue);
    if (isNaN(val) || val < 0 || val > 100) {
      setMessage({
        type: 'error',
        text: 'Threshold must be a number between 0 and 100.',
      });
      return;
    }

    setLoading(true);
    try {
      const result = await updateConfig(val);
      setThreshold(result.threshold);
      setInputValue(String(result.threshold));
      setMessage({ type: 'success', text: `Threshold updated to ${result.threshold}°C` });
      if (onThresholdChange) onThresholdChange(result.threshold);
      setTimeout(() => setMessage(null), 3000);
    } catch (err) {
      setMessage({ type: 'error', text: err.message });
      setInputValue(String(threshold));
    } finally {
      setLoading(false);
    }
  };

  const hasChanged = parseFloat(inputValue) !== threshold;

  return (
    <>
      <div className="threshold-card card">
        <div className="card-header">
          <h2 className="card-title">
            <Settings size={18} color="#2563eb" style={{ display: 'inline', marginRight: 8, verticalAlign: 'middle' }} />
            Alert Threshold
          </h2>
          <span className="current-threshold-badge">
            Current: {threshold}°C
          </span>
        </div>

        {error && (
          <div className="alert alert-warning" style={{ marginBottom: 'var(--spacing-md)' }}>
            <span>Failed to load config: {error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="threshold-form">
          <div className="form-group">
            <label htmlFor="threshold-input" className="label">
              Trigger Threshold (°C)
            </label>
            <div className="threshold-input-row">
              <input
                id="threshold-input"
                type="number"
                className="input threshold-input"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                min="0"
                max="100"
                step="0.5"
                placeholder="0–100"
                disabled={loading}
              />
              <button
                id="threshold-save"
                type="submit"
                className="button button-primary"
                disabled={loading || !hasChanged}
              >
                {loading ? (
                  'Saving…'
                ) : (
                  <>
                    <Check size={15} />
                    Save
                  </>
                )}
              </button>
              {hasChanged && (
                <button
                  type="button"
                  className="button"
                  onClick={() => {
                    setInputValue(String(threshold));
                    setMessage(null);
                  }}
                  title="Revert to current value"
                >
                  <X size={15} />
                </button>
              )}
            </div>
          </div>

          {message && (
            <div
              className={`alert ${message.type === 'success' ? 'alert-success' : 'alert-danger'}`}
            >
              <span>{message.text}</span>
            </div>
          )}

          <p className="threshold-hint">
            Alerts fire automatically whenever incoming sensor readings exceed this value.
          </p>
        </form>
      </div>

      <style>{`
        .threshold-card {
          background: #ffffff;
        }

        .threshold-card .card-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: var(--spacing-sm);
        }

        .current-threshold-badge {
          font-size: var(--font-size-xs);
          color: var(--color-accent-primary);
          background: #eff6ff;
          border: 1px solid #bfdbfe;
          padding: 3px 10px;
          border-radius: var(--radius-full);
          font-weight: 600;
        }

        .threshold-form {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-md);
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: var(--spacing-sm);
        }

        .threshold-input-row {
          display: flex;
          gap: var(--spacing-sm);
          align-items: center;
        }

        .threshold-input {
          flex: 1;
          max-width: 180px;
        }

        .threshold-hint {
          font-size: var(--font-size-xs);
          color: var(--color-text-muted);
          margin: 0;
          line-height: 1.4;
        }
      `}</style>
    </>
  );
}
