"""
Logwatch executor module.
Runs logwatch command and captures output.
"""
import subprocess
import logging
from typing import Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LogwatchExecutor:
    """Executes logwatch and returns structured output."""

    def __init__(self, logwatch_detail: str = "medium", timeout: int = 60):
        """
        Initialize logwatch executor.

        Args:
            logwatch_detail: Detail level (low, medium, high)
            timeout: Command timeout in seconds
        """
        self.logwatch_detail = logwatch_detail
        self.timeout = timeout

    def execute(self, services: list = None) -> Optional[str]:
        """
        Execute logwatch command and return output.

        Args:
            services: List of service names to monitor (e.g., ['messages', 'sshd'])

        Returns:
            logwatch output as string, or None if command failed
        """
        try:
            # Build logwatch command
            cmd = [
                "logwatch",
                "--detail", self.logwatch_detail,
                "--format", "text",  # Ensure text format
            ]

            # Add services if specified
            if services:
                service_str = ",".join(services)
                cmd.extend(["--logfile", service_str])

            # Add date range (yesterday if running daily)
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            cmd.extend(["--since", yesterday])

            logger.info(f"Executing logwatch: {' '.join(cmd)}")

            # Execute command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False  # Don't raise exception on non-zero exit code
            )

            if result.returncode != 0:
                logger.warning(f"logwatch exited with code {result.returncode}")
                if result.stderr:
                    logger.error(f"logwatch stderr: {result.stderr}")

            if result.stdout:
                logger.info(f"logwatch output length: {len(result.stdout)} characters")
                return result.stdout
            else:
                logger.warning("logwatch returned empty output")
                return None

        except subprocess.TimeoutExpired:
            logger.error(f"logwatch command timed out after {self.timeout} seconds")
            return None
        except FileNotFoundError:
            logger.error("logwatch command not found. Please install logwatch first.")
            return None
        except Exception as e:
            logger.error(f"Error executing logwatch: {e}", exc_info=True)
            return None

    def execute_simple(self) -> Optional[str]:
        """
        Execute logwatch with basic settings (all services, medium detail).

        Returns:
            logwatch output as string, or None if failed
        """
        return self.execute()

    def execute_for_service(self, service: str) -> Optional[str]:
        """
        Execute logwatch for a specific service.

        Args:
            service: Service name (e.g., 'sshd', 'apache-access')

        Returns:
            logwatch output for service, or None if failed
        """
        return self.execute(services=[service])


def format_logwatch_output_to_html(text: str) -> str:
    """
    Convert plain logwatch output to HTML format.

    Args:
        text: Plain text logwatch output

    Returns:
        HTML formatted output
    """
    # Escape HTML special characters
    text = (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

    # Convert newlines to <br /> tags
    html = f"""
    <div style="font-family: monospace; font-size: 12px; white-space: pre-wrap; background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
    {text}
    </div>
    """

    return html
