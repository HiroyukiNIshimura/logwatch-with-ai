"""
Unit tests for config module.
"""
import pytest
import os
import tempfile
from pathlib import Path
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


def test_config_get_services_list():
    """Test that services list is properly parsed."""
    with patch.dict(os.environ, {
        "DEEPSEEK_API_KEY": "test-key",
        "ADMIN_EMAIL": "admin@example.com",
        "LOGWATCH_SERVICES": "messages, sshd, apache-access"
    }):
        from src.config import Config
        config = Config()
        services = config.get_logwatch_services_list()
        assert len(services) == 3
        assert services[0] == "messages"
        assert services[2] == "apache-access"
