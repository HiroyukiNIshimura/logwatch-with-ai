"""
Email sender module.
Sends reports via local SMTP (postfix) with fallback to file storage.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class EmailSender:
    """Sends emails via local SMTP server with fallback to file storage."""

    def __init__(self, smtp_host: str = "localhost", smtp_port: int = 25):
        """
        Initialize email sender.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port

    def send_email(
        self,
        subject: str,
        body_html: str,
        recipient: str,
        sender: str = "logwatch-ai@localhost"
    ) -> bool:
        """
        Send email via SMTP.

        Args:
            subject: Email subject
            body_html: HTML email body
            recipient: Recipient email address
            sender: Sender email address

        Returns:
            True if sent successfully, False otherwise
        """
        try:
            logger.info(f"Sending email to {recipient}: {subject}")

            # Create MIME message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = sender
            message["To"] = recipient
            message["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

            # Attach HTML body
            html_part = MIMEText(body_html, "html", "utf-8")
            message.attach(html_part)

            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=10) as server:
                server.sendmail(sender, recipient, message.as_string())

            logger.info(f"Email sent successfully to {recipient}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            return False
        except ConnectionRefusedError:
            logger.error(f"Could not connect to SMTP server {self.smtp_host}:{self.smtp_port}")
            return False
        except Exception as e:
            logger.error(f"Error sending email: {e}", exc_info=True)
            return False

    def fallback_save_report(
        self,
        content: str,
        output_dir: str = "/var/tmp",
        prefix: str = "logwatch-report"
    ) -> Optional[str]:
        """
        Save report to file as fallback when email fails.

        Args:
            content: Report content (HTML)
            output_dir: Directory to save report
            prefix: Filename prefix

        Returns:
            Path to saved file, or None if save failed
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{prefix}-{timestamp}.html"
            filepath = output_path / filename

            # Write content to file
            with open(filepath, "w", encoding="utf-8") as f:
                # Wrap HTML with proper structure
                full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{prefix}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .warning {{ color: #ff6600; }}
        .error {{ color: #cc0000; }}
        pre {{ background-color: #f5f5f5; padding: 10px; overflow-x: auto; }}
    </style>
</head>
<body>
{content}
</body>
</html>"""
                f.write(full_html)

            logger.warning(f"Report saved to fallback file: {filepath}")
            return str(filepath)

        except PermissionError:
            logger.error(f"Permission denied writing to {output_dir}")
            return None
        except Exception as e:
            logger.error(f"Error saving report to file: {e}", exc_info=True)
            return None


def format_json_analysis_to_html(analysis: dict, raw_logwatch_output: str = "") -> str:
    """
    Convert DeepSeek JSON analysis to HTML email body.

    Args:
        analysis: Dictionary with analysis results from DeepSeek
        raw_logwatch_output: Raw logwatch output to append

    Returns:
        HTML formatted email body
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""
    <h2>System Log Analysis Report</h2>
    <p><small>Generated: {timestamp}</small></p>
    <p><strong>Status:</strong> <span style="color: green;">Analysis completed by DeepSeek</span></p>

    <hr>

    <h3>Summary</h3>
    <p>{analysis.get('summary', 'No summary available')}</p>

    <h3>Critical Issues</h3>
    """

    critical_issues = analysis.get("critical_issues", [])
    if critical_issues:
        html += "<ul>"
        for issue in critical_issues:
            html += f"<li style='color: #cc0000;'>{issue}</li>"
        html += "</ul>"
    else:
        html += "<p><em>No critical issues detected.</em></p>"

    html += """
    <h3>Security Alerts</h3>
    """

    security_alerts = analysis.get("security_alerts", [])
    if security_alerts:
        html += "<ul>"
        for alert in security_alerts:
            html += f"<li style='color: #ff6600;'>{alert}</li>"
        html += "</ul>"
    else:
        html += "<p><em>No security alerts.</em></p>"

    html += """
    <h3>Performance Issues</h3>
    """

    perf_issues = analysis.get("performance_issues", [])
    if perf_issues:
        html += "<ul>"
        for issue in perf_issues:
            html += f"<li>{issue}</li>"
        html += "</ul>"
    else:
        html += "<p><em>No performance issues detected.</em></p>"

    html += """
    <h3>Important Warnings</h3>
    """

    warnings = analysis.get("important_warnings", [])
    if warnings:
        html += "<ul>"
        for warning in warnings:
            html += f"<li>{warning}</li>"
        html += "</ul>"
    else:
        html += "<p><em>No important warnings.</em></p>"

    html += """
    <h3>Recommendations</h3>
    """

    recommendations = analysis.get("recommendations", [])
    if recommendations:
        html += "<ol>"
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        html += "</ol>"
    else:
        html += "<p><em>No specific recommendations.</em></p>"

    if raw_logwatch_output:
        escaped_output = (raw_logwatch_output
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
        html += f"""
        <hr>
        <h3>Raw Logwatch Output</h3>
        <details>
          <summary>Click to expand raw output</summary>
          <pre style="font-family: monospace; font-size: 12px; background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto; white-space: pre-wrap;">
{escaped_output}
          </pre>
        </details>
        """

    html += """
    <hr>
    <p><small>Generated by logwatch-with-ai | Powered by DeepSeek</small></p>
    """

    return html


def format_raw_logwatch_to_html(logwatch_output: str, failure_reason: str = "") -> str:
    """
    Convert raw logwatch output to HTML email body (fallback when DeepSeek fails).

    Args:
        logwatch_output: Plain text logwatch output
        failure_reason: Reason for using raw output

    Returns:
        HTML formatted email body
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Escape HTML special characters
    escaped_output = (logwatch_output
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )

    reason_text = f"<p style='color: #ff6600;'><strong>Note:</strong> {failure_reason}</p>" if failure_reason else ""

    html = f"""
    <h2>System Log Report</h2>
    <p><small>Generated: {timestamp}</small></p>
    <p><strong>Status:</strong> <span style="color: #ff6600;">Raw logwatch output (analysis unavailable)</span></p>
    {reason_text}

    <hr>

    <h3>Logwatch Output</h3>
    <pre style="font-family: monospace; font-size: 12px; background-color: #f5f5f5; padding: 10px; border-radius: 5px; overflow-x: auto;">
{escaped_output}
    </pre>

    <hr>
    <p><small>Generated by logwatch-with-ai | DeepSeek analysis unavailable</small></p>
    """

    return html
