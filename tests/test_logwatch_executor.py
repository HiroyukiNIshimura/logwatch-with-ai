"""
Unit tests for logwatch executor module.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.logwatch_executor import LogwatchExecutor, format_logwatch_output_to_html


def test_logwatch_executor_initialization():
    """Test LogwatchExecutor initialization."""
    executor = LogwatchExecutor(logwatch_detail="high", timeout=30)
    assert executor.logwatch_detail == "high"
    assert executor.timeout == 30


@patch("src.logwatch_executor.subprocess.run")
def test_execute_simple(mock_run):
    """Test simple logwatch execution."""
    mock_run.return_value = MagicMock(returncode=0, stdout="log output", stderr="")

    executor = LogwatchExecutor()
    result = executor.execute()

    assert result == "log output"
    mock_run.assert_called_once()


@patch("src.logwatch_executor.subprocess.run")
def test_execute_with_services(mock_run):
    """Test logwatch execution with specific services."""
    mock_run.return_value = MagicMock(returncode=0, stdout="service output", stderr="")

    executor = LogwatchExecutor()
    result = executor.execute(services=["sshd", "apache-access"])

    assert result == "service output"
    call_args = mock_run.call_args
    assert "sshd,apache-access" in call_args[0][0]


@patch("src.logwatch_executor.subprocess.run")
def test_execute_timeout(mock_run):
    """Test logwatch timeout handling."""
    import subprocess
    mock_run.side_effect = subprocess.TimeoutExpired("logwatch", 30)

    executor = LogwatchExecutor(timeout=30)
    result = executor.execute()

    assert result is None


def test_format_logwatch_output_to_html():
    """Test HTML formatting of logwatch output."""
    input_text = "<script>alert('xss')</script>\n\nLog line 1\nLog line 2"
    result = format_logwatch_output_to_html(input_text)

    assert "&lt;script&gt;" in result
    assert "&lt;/script&gt;" in result
    assert "<br />" in result or "<br/>" in result
    assert "monospace" in result
