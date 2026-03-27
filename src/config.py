"""
Configuration management module.
Loads and validates environment variables and provides default values.
"""
import os
import logging
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

logger = logging.getLogger(__name__)


class Config:
    """Configuration handler for logwatch-ai application."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        self._load_dotenv_if_present()

        # AI Provider
        self.ai_provider = os.getenv("AI_PROVIDER", "deepseek").strip().lower()

        # Provider API keys
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        # Provider models
        self.deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

        # API execution tuning
        self.deepseek_max_retries = int(os.getenv("DEEPSEEK_MAX_RETRIES", "3"))
        self.deepseek_timeout = int(os.getenv("DEEPSEEK_TIMEOUT", "30"))
        self.deepseek_retry_backoff = float(os.getenv("DEEPSEEK_RETRY_BACKOFF_FACTOR", "2"))
        self.deepseek_max_input_chars = int(os.getenv("DEEPSEEK_MAX_INPUT_CHARS", "50000"))

        # Resolved provider values
        self.ai_api_key = self._resolve_ai_api_key()
        self.ai_model = self._resolve_ai_model()

        # Email (SMTP)
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "25"))
        self.mail_from = os.getenv("MAIL_FROM", "logwatch-ai@localhost")
        self.admin_email = os.getenv("ADMIN_EMAIL")

        # Output
        self.report_output_dir = os.getenv("ANALYZED_REPORT_OUTPUT", "/var/tmp")

        # Logging
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.script_log_file = os.getenv("SCRIPT_LOG_FILE", "/var/log/logwatch-ai.log")

        # Validate critical configuration
        self._validate()

    def _validate(self) -> None:
        """Validate required configuration values."""
        if self.ai_provider not in ["deepseek", "openai", "gemini"]:
            raise ValueError("AI_PROVIDER must be one of: deepseek, openai, gemini")

        if not self.ai_api_key:
            provider_env_map = {
                "deepseek": "DEEPSEEK_API_KEY",
                "openai": "OPENAI_API_KEY",
                "gemini": "GEMINI_API_KEY",
            }
            required_env = provider_env_map.get(self.ai_provider, "API_KEY")
            raise ValueError(f"{required_env} environment variable is required for provider '{self.ai_provider}'")

        if not self.admin_email:
            raise ValueError("ADMIN_EMAIL environment variable is required")

        # Check if output directory exists and is writable
        report_path = Path(self.report_output_dir)
        if not report_path.exists():
            try:
                report_path.mkdir(parents=True, mode=0o755)
                logger.info(f"Created report output directory: {self.report_output_dir}")
            except OSError as e:
                logger.warning(f"Could not create report output directory: {e}")
        else:
            if not os.access(self.report_output_dir, os.W_OK):
                logger.warning(f"Report output directory not writable: {self.report_output_dir}")

    def _load_dotenv_if_present(self) -> None:
        """Load .env from project root if available."""
        try:
            project_root = Path(__file__).resolve().parent.parent
            dotenv_path = project_root / ".env"
            if dotenv_path.exists():
                if load_dotenv is not None:
                    load_dotenv(dotenv_path=dotenv_path, override=False)
                    logger.debug(f"Loaded environment variables from {dotenv_path} via python-dotenv")
                else:
                    # Fallback parser when python-dotenv is not installed
                    self._load_dotenv_fallback(dotenv_path)
                    logger.debug(f"Loaded environment variables from {dotenv_path} via fallback parser")
        except Exception as e:
            logger.warning(f"Could not load .env file: {e}")

    def _load_dotenv_fallback(self, dotenv_path: Path) -> None:
        """Minimal .env loader without external dependency."""
        with dotenv_path.open("r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue

                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                # Do not overwrite already-exported environment variables
                os.environ.setdefault(key, value)

    def _resolve_ai_api_key(self) -> str:
        """Resolve active API key from selected provider."""
        provider_key_map = {
            "deepseek": self.deepseek_api_key,
            "openai": self.openai_api_key,
            "gemini": self.gemini_api_key,
        }
        return provider_key_map.get(self.ai_provider)

    def _resolve_ai_model(self) -> str:
        """Resolve active model from selected provider."""
        provider_model_map = {
            "deepseek": self.deepseek_model,
            "openai": self.openai_model,
            "gemini": self.gemini_model,
        }
        return provider_model_map.get(self.ai_provider)

    def to_dict(self) -> dict:
        """Return configuration as dictionary (safe for logging, excludes secrets)."""
        return {
            "ai_provider": self.ai_provider,
            "ai_model": self.ai_model,
            "ai_api_key": "***" if self.ai_api_key else None,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "admin_email": self.admin_email,
            "report_output_dir": self.report_output_dir,
            "log_level": self.log_level,
            "deepseek_max_input_chars": self.deepseek_max_input_chars,
        }


def setup_logging(log_file: str, log_level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Args:
        log_file: Path to log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logger.debug(f"Logging configured: level={log_level}, file={log_file}")
