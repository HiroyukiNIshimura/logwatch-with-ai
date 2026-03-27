"""
Unit tests for email sender module.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.email_sender import (
    EmailSender,
    format_json_analysis_to_html,
    format_raw_logwatch_to_html
)


def test_email_sender_initialization():
    """Test EmailSender initialization."""
    sender = EmailSender(smtp_host="mail.example.com", smtp_port=587)
    assert sender.smtp_host == "mail.example.com"
    assert sender.smtp_port == 587


@patch("src.email_sender.smtplib.SMTP")
def test_send_email_success(mock_smtp):
    """Test successful email sending."""
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    sender = EmailSender()
    result = sender.send_email(
        subject="Test",
        body_html="<p>Test</p>",
        recipient="user@example.com"
    )

    assert result is True
    mock_server.sendmail.assert_called_once()


@patch("src.email_sender.smtplib.SMTP")
def test_send_email_failure(mock_smtp):
    """Test email send failure."""
    mock_smtp.side_effect = ConnectionRefusedError()

    sender = EmailSender()
    result = sender.send_email(
        subject="Test",
        body_html="<p>Test</p>",
        recipient="user@example.com"
    )

    assert result is False


def test_fallback_save_report():
    """Test fallback report saving."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sender = EmailSender()
        result = sender.fallback_save_report(
            content="<p>Test report</p>",
            output_dir=tmpdir,
            prefix="test"
        )

        assert result is not None
        assert Path(result).exists()

        with open(result, "r") as f:
            content = f.read()
            assert "<p>Test report</p>" in content
            assert "<!DOCTYPE html>" in content


def test_format_json_analysis_to_html():
    """Test JSON analysis formatting to HTML."""
    analysis = {
        "summary": "System is healthy",
        "critical_issues": ["Issue 1"],
        "security_alerts": ["Alert 1"],
        "performance_issues": [],
        "important_warnings": [],
        "recommendations": ["Rec 1"]
    }

    html = format_json_analysis_to_html(analysis, "RAW <log> line")

    assert "<h2>" in html
    assert "System is healthy" in html
    assert "Issue 1" in html
    assert "Alert 1" in html
    assert "Rec 1" in html
    assert "Raw Logwatch Output" in html
    assert "RAW &lt;log&gt; line" in html


def test_format_raw_logwatch_to_html():
    """Test raw logwatch output formatting."""
    logwatch_output = "Error: Something failed\nWarning: Check this"

    html = format_raw_logwatch_to_html(logwatch_output, "API unavailable")

    assert "<h2>" in html
    assert "API unavailable" in html
    assert "Something failed" in html
    assert "<pre" in html
