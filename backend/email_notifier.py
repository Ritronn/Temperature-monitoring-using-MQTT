"""
Email Notification Service for ThermosenseIoT Dashboard.

Sends email alerts via SMTP when temperature readings exceed configured thresholds.
Designed to run asynchronously using a thread pool so it never blocks MQTT message
reception or WebSocket broadcasting.
"""

import concurrent.futures
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict, Optional

logger = logging.getLogger("thermosense.email")


class EmailNotifier:
    """
    SMTP-based alert email notification service.

    Sends formatted plain-text and HTML emails when high-temperature alerts occur.
    Dispatches sending to a background thread to prevent blocking the calling thread.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the email notifier with SMTP configuration.

        Args:
            config: Dictionary containing SMTP parameters:
                - host (str): SMTP server hostname (default: smtp.gmail.com)
                - port (int): SMTP server port (default: 587)
                - user (str): SMTP username / sender address
                - password (str): SMTP password / app password
                - recipient (str): Alert recipient email address
                - use_tls (bool): Whether to use STARTTLS (default: True)
                - enabled (bool): Master switch for email notifications (default: True)
        """
        cfg = config or {}
        self.host = cfg.get("host", "smtp.gmail.com")
        self.port = int(cfg.get("port", 587))
        self.user = cfg.get("user", "gojoritron@gmail.com")
        self.password = cfg.get("password", "zvgtzzrwkztumdwk")
        self.recipient = cfg.get("recipient", "rutvikkale2006@gmail.com")
        self.use_tls = cfg.get("use_tls", True)
        self.enabled = cfg.get("enabled", True)

        # Thread pool for asynchronous email dispatch
        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=2,
            thread_name_prefix="email-notifier",
        )

        logger.info(
            f"EmailNotifier initialized: enabled={self.enabled}, "
            f"host={self.host}:{self.port}, sender={self.user}, recipient={self.recipient}"
        )

    def send_alert_email(self, alert: Any) -> concurrent.futures.Future:
        """
        Asynchronously dispatch a high-temperature alert email.

        Args:
            alert: AlertEvent model or dict containing:
                   device_id, temperature, threshold, timestamp

        Returns:
            concurrent.futures.Future of the email sending task
        """
        if not self.enabled:
            logger.debug("Email notification skipped: SMTP is disabled")
            return self._executor.submit(lambda: False)

        device_id = getattr(alert, "device_id", None) or (alert.get("device_id") if isinstance(alert, dict) else "unknown")
        temperature = getattr(alert, "temperature", None) or (alert.get("temperature") if isinstance(alert, dict) else 0.0)
        threshold = getattr(alert, "threshold", None) or (alert.get("threshold") if isinstance(alert, dict) else 0.0)
        timestamp = getattr(alert, "timestamp", None) or (alert.get("timestamp") if isinstance(alert, dict) else "")

        return self._executor.submit(
            self._send_email_sync,
            device_id=device_id,
            temperature=float(temperature),
            threshold=float(threshold),
            timestamp=str(timestamp),
        )

    def _send_email_sync(
        self,
        device_id: str,
        temperature: float,
        threshold: float,
        timestamp: str,
    ) -> bool:
        """
        Synchronously format and send the alert email over SMTP.

        Executed in a background worker thread.
        """
        if not self.user or not self.password or not self.recipient:
            logger.warning("Email notification skipped: Missing SMTP credentials or recipient")
            return False

        try:
            delta = temperature - threshold
            subject = f"🔥 [Thermosense ALERT] High Temperature: {temperature:.1f}°C on {device_id}"

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"Thermosense Alert System <{self.user}>"
            msg["To"] = self.recipient

            # Plain text fallback
            text_content = (
                f"THERMOSENSE IOT TEMPERATURE ALERT\n"
                f"==================================\n\n"
                f"A high temperature alert was triggered on device '{device_id}'.\n\n"
                f"• Device ID:    {device_id}\n"
                f"• Temperature:  {temperature:.2f}°C\n"
                f"• Threshold:    {threshold:.2f}°C\n"
                f"• Delta:        +{delta:.2f}°C above threshold\n"
                f"• Timestamp:    {timestamp}\n\n"
                f"View Dashboard: http://localhost:5173\n"
            )

            # Polished HTML template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
              <meta charset="utf-8">
              <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #0f172a; }}
                .container {{ max-width: 560px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
                .header {{ background: #dc2626; padding: 20px 24px; color: #ffffff; }}
                .header h1 {{ margin: 0; font-size: 20px; font-weight: 700; letter-spacing: -0.01em; }}
                .header p {{ margin: 4px 0 0; font-size: 13px; opacity: 0.9; }}
                .body {{ padding: 24px; }}
                .metric-box {{ background: #fef2f2; border: 1px solid #fecaca; border-radius: 8px; padding: 16px; margin-bottom: 20px; text-align: center; }}
                .metric-label {{ font-size: 12px; color: #991b1b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; }}
                .metric-value {{ font-size: 38px; font-weight: 800; color: #dc2626; margin: 6px 0; }}
                .metric-delta {{ font-size: 13px; color: #b91c1c; font-weight: 600; }}
                .details-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                .details-table td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; font-size: 14px; }}
                .details-table td:first-child {{ color: #64748b; font-weight: 500; width: 35%; }}
                .details-table td:last-child {{ color: #0f172a; font-weight: 600; }}
                .btn {{ display: inline-block; background: #2563eb; color: #ffffff !important; text-decoration: none; padding: 10px 20px; border-radius: 6px; font-size: 14px; font-weight: 600; text-align: center; }}
                .footer {{ background: #f8fafc; padding: 16px 24px; border-top: 1px solid #e2e8f0; font-size: 12px; color: #94a3b8; text-align: center; }}
              </style>
            </head>
            <body>
              <div class="container">
                <div class="header">
                  <h1>⚠️ High Temperature Alert</h1>
                  <p>ThermosenseIoT Telemetry Warning System</p>
                </div>
                <div class="body">
                  <div class="metric-box">
                    <div class="metric-label">Recorded Temperature</div>
                    <div class="metric-value">{temperature:.1f}°C</div>
                    <div class="metric-delta">+{delta:.1f}°C above threshold ({threshold:.1f}°C)</div>
                  </div>
                  <table class="details-table">
                    <tr>
                      <td>Device Identifier</td>
                      <td><code>{device_id}</code></td>
                    </tr>
                    <tr>
                      <td>Alert Threshold</td>
                      <td>{threshold:.1f}°C</td>
                    </tr>
                    <tr>
                      <td>Recorded Reading</td>
                      <td><strong style="color: #dc2626;">{temperature:.2f}°C</strong></td>
                    </tr>
                    <tr>
                      <td>Timestamp</td>
                      <td>{timestamp}</td>
                    </tr>
                    <tr>
                      <td>Status</td>
                      <td><span style="color: #dc2626; font-weight: 700;">ACTIVE CRITICAL</span></td>
                    </tr>
                  </table>
                  <div style="text-align: center; margin-top: 16px;">
                    <a href="http://localhost:5173" class="btn">Open Thermosense Dashboard</a>
                  </div>
                </div>
                <div class="footer">
                  This is an automated notification from your ThermosenseIoT monitoring system.<br>
                  Sender: {self.user} · Target: {self.recipient}
                </div>
              </div>
            </body>
            </html>
            """

            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))

            logger.info(f"Connecting to SMTP server {self.host}:{self.port} to send alert email...")
            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)

            logger.info(
                f"Successfully sent alert email to {self.recipient} for device {device_id} ({temperature}°C)"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send alert email to {self.recipient}: {e}", exc_info=True)
            return False

    def shutdown(self) -> None:
        """Shutdown the background thread pool gracefully."""
        self._executor.shutdown(wait=False)
