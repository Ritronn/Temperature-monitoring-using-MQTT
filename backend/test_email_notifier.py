"""
Tests for EmailNotifier module.
"""

from unittest.mock import MagicMock, patch
from email_notifier import EmailNotifier
from models import AlertEvent


def test_email_notifier_initialization():
    config = {
        "host": "smtp.example.com",
        "port": 587,
        "user": "test@example.com",
        "password": "secretpassword",
        "recipient": "alert@example.com",
        "use_tls": True,
        "enabled": True,
    }
    notifier = EmailNotifier(config)
    assert notifier.host == "smtp.example.com"
    assert notifier.port == 587
    assert notifier.user == "test@example.com"
    assert notifier.recipient == "alert@example.com"
    assert notifier.enabled is True
    notifier.shutdown()


def test_email_notifier_disabled():
    notifier = EmailNotifier({"enabled": False})
    future = notifier.send_alert_email({"device_id": "sensor-001", "temperature": 40.0, "threshold": 35.0, "timestamp": "2026-10-27T12:00:00Z"})
    assert future.result() is False
    notifier.shutdown()


@patch("smtplib.SMTP")
def test_send_alert_email_success(mock_smtp):
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    notifier = EmailNotifier({
        "host": "smtp.gmail.com",
        "port": 587,
        "user": "gojoritron@gmail.com",
        "password": "zvgtzzrwkztumdwk",
        "recipient": "rutvikkale2006@gmail.com",
        "use_tls": True,
        "enabled": True,
    })

    alert = AlertEvent(
        device_id="sensor-001",
        temperature=42.5,
        threshold=35.0,
        alert_type="high_temperature",
        timestamp="2026-10-27T14:00:00Z",
        resolved=False,
    )

    future = notifier.send_alert_email(alert)
    result = future.result(timeout=5)

    assert result is True
    mock_server.starttls.assert_called_once()
    mock_server.login.assert_called_once_with("gojoritron@gmail.com", "zvgtzzrwkztumdwk")
    mock_server.send_message.assert_called_once()
    notifier.shutdown()
