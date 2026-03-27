"""
Unit tests for logwatch executor module.
"""
import pytest
from unittest.mock import patch, MagicMock
from src.logwatch_executor import LogwatchExecutor, format_logwatch_output_to_html


def test_logwatch_executor_initialization():
    """Test LogwatchExecutor initialization."""
    executor = LogwatchExecutor(timeout=30)
    assert executor.timeout == 30


@patch("src.logwatch_executor.subprocess.run")
def test_execute_simple(mock_run):
    """Test simple logwatch execution."""
    mock_run.return_value = MagicMock(returncode=0, stdout="log output", stderr="")

    executor = LogwatchExecutor()
    result = executor.execute()

    assert result == "log output"
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[0][0] == ["logwatch", "--format", "text"]


@patch("src.logwatch_executor.subprocess.run")
def test_execute_command_has_only_format_option(mock_run):
    """Test logwatch execution uses only --format runtime option."""
    mock_run.return_value = MagicMock(returncode=0, stdout="service output", stderr="")

    executor = LogwatchExecutor()
    result = executor.execute()

    assert result == "service output"
    call_args = mock_run.call_args
    assert call_args[0][0] == ["logwatch", "--format", "text"]


@patch("src.logwatch_executor.subprocess.run")
def test_execute_timeout(mock_run):
    """Test logwatch timeout handling."""
    import subprocess
    mock_run.side_effect = subprocess.TimeoutExpired("logwatch", 30)

    executor = LogwatchExecutor(timeout=30)
    result = executor.execute()

    assert result is None


@patch("src.logwatch_executor.subprocess.run")
def test_execute_empty_output_returns_none(mock_run):
    """Test that whitespace-only output is treated as empty."""
    mock_run.return_value = MagicMock(returncode=0, stdout="   \n\t", stderr="")

    executor = LogwatchExecutor()
    result = executor.execute()

    assert result is None


def test_format_logwatch_output_to_html():
    """Test HTML formatting of logwatch output."""
    input_text = "<script>alert('xss')</script>\n\nLog line 1\nLog line 2"
    result = format_logwatch_output_to_html(input_text)

    assert "&lt;script&gt;" in result
    assert "&lt;/script&gt;" in result
    assert "monospace" in result
