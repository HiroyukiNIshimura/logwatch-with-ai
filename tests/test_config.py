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


def test_config_to_dict_masks_secrets():
    """Test that to_dict masks API key and exposes safe fields."""
    with patch.dict(os.environ, {
        "DEEPSEEK_API_KEY": "test-key",
        "ADMIN_EMAIL": "admin@example.com"
    }):
        from src.config import Config
        config = Config()
        data = config.to_dict()
        assert data["deepseek_api_key"] == "***"
        assert data["admin_email"] == "admin@example.com"
