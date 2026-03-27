"""
Unit tests for DeepSeek analyzer module.
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from src.deepseek_analyzer import AIAnalyzer


def test_analyzer_initialization():
    """Test AIAnalyzer initialization."""
    analyzer = AIAnalyzer(api_key="test-key", max_retries=3, timeout=30)
    assert analyzer.api_key == "test-key"
    assert analyzer.provider == "deepseek"
    assert analyzer.api_endpoint.endswith("/chat/completions")
    assert analyzer.model == "deepseek-chat"
    assert analyzer.max_retries == 3
    assert analyzer.timeout == 30
    assert analyzer.max_input_chars == 50000


def test_analyzer_provider_openai_initialization():
    """Test OpenAI provider initialization."""
    analyzer = AIAnalyzer(api_key="test-key", provider="openai", model="gpt-4o-mini")
    assert analyzer.provider == "openai"
    assert analyzer.api_endpoint == "https://api.openai.com/v1/chat/completions"
    assert analyzer.model == "gpt-4o-mini"


def test_analyzer_provider_gemini_initialization():
    """Test Gemini provider initialization."""
    analyzer = AIAnalyzer(api_key="test-key", provider="gemini")
    assert analyzer.provider == "gemini"
    assert analyzer.api_endpoint == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    assert analyzer.model == "gemini-2.0-flash"


def test_build_analysis_prompt():
    """Test prompt building."""
    analyzer = AIAnalyzer(api_key="test-key")
    prompt = analyzer._build_analysis_prompt("Test log output")

    assert "Test log output" in prompt
    assert "critical_issues" in prompt
    assert "security_alerts" in prompt
    assert "日本語" in prompt


@patch("src.deepseek_analyzer.requests.post")
def test_analyze_success(mock_post):
    """Test successful analysis."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"critical_issues": [], "security_alerts": []}'}}]
    }
    mock_post.return_value = mock_response

    analyzer = AIAnalyzer(api_key="test-key")
    result = analyzer.analyze("Test log")

    assert result is not None
    assert isinstance(result, dict)


@patch("src.deepseek_analyzer.requests.post")
def test_analyze_api_error(mock_post):
    """Test handling of API errors."""
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_post.return_value = mock_response

    analyzer = AIAnalyzer(api_key="invalid-key", max_retries=1)
    result = analyzer.analyze("Test log")

    assert result is None


def test_parse_response_valid_json():
    """Test parsing valid JSON response."""
    analyzer = AIAnalyzer(api_key="test-key")

    response_text = '{"critical_issues": ["error1"], "security_alerts": []}'
    result = analyzer._parse_response(response_text)

    assert result is not None
    assert "critical_issues" in result


def test_parse_response_invalid_json():
    """Test parsing invalid JSON response."""
    analyzer = AIAnalyzer(api_key="test-key")

    response_text = "This is not JSON"
    result = analyzer._parse_response(response_text)

    assert result is None


def test_calculate_backoff():
    """Test exponential backoff calculation."""
    analyzer = AIAnalyzer(api_key="test-key", retry_backoff=2.0)

    assert analyzer._calculate_backoff(0) == 1.0
    assert analyzer._calculate_backoff(1) == 2.0
    assert analyzer._calculate_backoff(2) == 4.0


def test_compact_logwatch_output_truncates_large_input():
    """Test compaction for oversized log input."""
    analyzer = AIAnalyzer(api_key="test-key", max_input_chars=1000)
    large_log = ("INFO normal line\n" * 200) + ("ERROR failed login\n" * 200)

    compacted = analyzer._compact_logwatch_output(large_log)

    assert len(compacted) <= 1000
    assert "TRUNCATED LOGWATCH OUTPUT" in compacted


def test_compact_logwatch_output_keeps_small_input():
    """Test small input remains unchanged."""
    analyzer = AIAnalyzer(api_key="test-key", max_input_chars=1000)
    small_log = "INFO hello\nWARN test"

    compacted = analyzer._compact_logwatch_output(small_log)

    assert compacted == small_log
