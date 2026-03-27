"""
Unit tests for config module.
"""
import pytest
import os
from unittest.mock import patch


def test_config_initialization():
    """Test that config initializes with environment variables."""
    with patch.dict(os.environ, {
        "DEEPSEEK_API_KEY": "test-key",
        "ADMIN_EMAIL": "admin@example.com"
    }):
        from src.config import Config
        config = Config()
        assert config.deepseek_api_key == "test-key"
        assert config.ai_provider == "deepseek"
        assert config.ai_api_key == "test-key"
        assert config.admin_email == "admin@example.com"


def test_config_validation_missing_api_key():
    """Test that config raises error when API key is missing."""
    with patch.dict(os.environ, {
        "ADMIN_EMAIL": "admin@example.com"
    }, clear=True):
        with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
            from src.config import Config
            config = Config()


def test_config_validation_missing_email():
    """Test that config raises error when email is missing."""
    with patch.dict(os.environ, {
        "DEEPSEEK_API_KEY": "test-key"
    }, clear=True):
        with pytest.raises(ValueError, match="ADMIN_EMAIL"):
            from src.config import Config
            config = Config()


def test_config_validation_missing_provider_key_openai():
    """Test that provider-specific key is required for OpenAI."""
    with patch.dict(os.environ, {
        "AI_PROVIDER": "openai",
        "ADMIN_EMAIL": "admin@example.com"
    }, clear=True):
        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            from src.config import Config
            config = Config()


def test_config_provider_openai_uses_openai_key_and_model():
    """Test provider resolution for OpenAI."""
    with patch.dict(os.environ, {
        "AI_PROVIDER": "openai",
        "OPENAI_API_KEY": "openai-test-key",
        "OPENAI_MODEL": "gpt-4o-mini",
        "ADMIN_EMAIL": "admin@example.com"
    }, clear=True):
        from src.config import Config
        config = Config()
        assert config.ai_provider == "openai"
        assert config.ai_api_key == "openai-test-key"
        assert config.ai_model == "gpt-4o-mini"


def test_config_to_dict_masks_secrets():
    """Test that to_dict masks API key and exposes safe fields."""
    with patch.dict(os.environ, {
        "DEEPSEEK_API_KEY": "test-key",
        "ADMIN_EMAIL": "admin@example.com"
    }):
        from src.config import Config
        config = Config()
        data = config.to_dict()
        assert data["ai_api_key"] == "***"
        assert data["admin_email"] == "admin@example.com"
