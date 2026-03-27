"""
Logwatch executor module.
Runs logwatch command and captures output.
"""
import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class LogwatchExecutor:
    """Executes logwatch and returns structured output."""

    def __init__(self, timeout: int = 60):
        """
        Initialize logwatch executor.

        Args:
            timeout: Command timeout in seconds
        """
        self.timeout = timeout

    def execute(self) -> Optional[str]:
        """
        Execute logwatch command and return output.

        Returns:
            logwatch output as string, or None if command failed
        """
        try:
            # Build logwatch command.
            # journald support and monitored services are configured in logwatch itself,
            # so this script intentionally uses only --format.
            cmd = [
                "logwatch",
                "--format", "text",  # Ensure text format
            ]

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
            elif result.stderr:
                logger.warning(f"logwatch stderr (code=0): {result.stderr}")

            if result.stdout and result.stdout.strip():
                logger.info(f"logwatch output length: {len(result.stdout)} characters")
                return result.stdout
            else:
                logger.warning(
                    "logwatch returned empty output. "
                    "Check logwatch configuration (Output = stdout), service filters, and log permissions."
                )
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
        Execute logwatch with configured defaults.

        Returns:
            logwatch output as string, or None if failed
        """
        return self.execute()


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
