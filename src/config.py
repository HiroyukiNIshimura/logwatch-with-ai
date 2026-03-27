"""
Configuration management module.
Loads and validates environment variables and provides default values.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class Config:
    """Configuration handler for logwatch-ai application."""

    def __init__(self):
        """Initialize configuration from environment variables."""
        self._load_dotenv_if_present()

        # DeepSeek API
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.deepseek_max_retries = int(os.getenv("DEEPSEEK_MAX_RETRIES", "3"))
        self.deepseek_timeout = int(os.getenv("DEEPSEEK_TIMEOUT", "30"))
        self.deepseek_retry_backoff = float(os.getenv("DEEPSEEK_RETRY_BACKOFF_FACTOR", "2"))

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
        if not self.deepseek_api_key:
            raise ValueError("DEEPSEEK_API_KEY environment variable is required")

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
                load_dotenv(dotenv_path=dotenv_path, override=False)
                logger.debug(f"Loaded environment variables from {dotenv_path}")
        except Exception as e:
            logger.warning(f"Could not load .env file: {e}")

    def to_dict(self) -> dict:
        """Return configuration as dictionary (safe for logging, excludes secrets)."""
        return {
            "deepseek_api_key": "***" if self.deepseek_api_key else None,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "admin_email": self.admin_email,
            "report_output_dir": self.report_output_dir,
            "log_level": self.log_level,
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
