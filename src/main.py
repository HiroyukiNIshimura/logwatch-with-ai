#!/usr/bin/env python3
"""
Logwatch with AI - Main orchestration script.
Executes logwatch → DeepSeek analysis → Email with fallback support.
"""
import sys
import logging
from datetime import datetime
from pathlib import Path

# Import modules
from config import Config, setup_logging
from logwatch_executor import LogwatchExecutor, format_logwatch_output_to_html
from deepseek_analyzer import AIAnalyzer
from email_sender import (
    EmailSender,
    format_json_analysis_to_html,
    format_raw_logwatch_to_html
)

logger = logging.getLogger(__name__)


def main():
    """Main orchestration function."""
    start_time = datetime.now()

    try:
        # ========== Step 1: Load Configuration ==========
        logger.info("=" * 60)
        logger.info("Starting logwatch-with-ai execution")
        logger.info("=" * 60)

        config = Config()
        logger.info(f"Configuration loaded: {config.to_dict()}")

        # ========== Step 2: Execute logwatch ==========
        logger.info("Executing logwatch...")
        logwatch_executor = LogwatchExecutor(timeout=60)
        logwatch_output = logwatch_executor.execute()

        if not logwatch_output:
            logger.error("logwatch produced no output. Aborting.")
            return 1

        logger.info(f"logwatch output: {len(logwatch_output)} characters")

        # ========== Step 3: DeepSeek Analysis (with fallback) ==========
        logger.info("Attempting DeepSeek analysis...")
        ai_analyzer = AIAnalyzer(
            api_key=config.ai_api_key,
            provider=config.ai_provider,
            model=config.ai_model,
            max_retries=config.deepseek_max_retries,
            timeout=config.deepseek_timeout,
            retry_backoff=config.deepseek_retry_backoff,
            max_input_chars=config.deepseek_max_input_chars
        )

        deepseek_result = ai_analyzer.analyze(logwatch_output)

        # ========== Step 4: Prepare Email Body ==========
        if deepseek_result is not None:
            # ✓ Success: Use DeepSeek analysis
            logger.info("DeepSeek analysis successful, using analyzed report")
            email_subject = "[LOGWATCH] System Analysis Report"
            email_body = format_json_analysis_to_html(deepseek_result, logwatch_output)
            analysis_status = "SUCCESS"
        else:
            # ✗ DeepSeek failed: Use raw logwatch output (FALLBACK 1)
            logger.warning("DeepSeek analysis failed, using raw logwatch output as fallback")
            email_subject = "[LOGWATCH] System Log Report (DeepSeek Unavailable)"
            email_body = format_raw_logwatch_to_html(
                logwatch_output,
                failure_reason="AI analysis (DeepSeek) is temporarily unavailable. Raw logwatch output is provided below."
            )
            analysis_status = "FALLBACK_RAW_OUTPUT"

        # ========== Step 5: Send Email (with fallback to file) ==========
        logger.info("Attempting to send email...")
        email_sender = EmailSender(
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port
        )

        mail_sent = email_sender.send_email(
            subject=email_subject,
            body_html=email_body,
            recipient=config.admin_email,
            sender=config.mail_from
        )

        if mail_sent:
            # ✓ Email sent successfully
            logger.info(f"Email sent successfully to {config.admin_email}")
            send_status = "EMAIL_SENT"
        else:
            # ✗ Email failed: Save to file (FALLBACK 2)
            logger.error("Email send failed, saving to file as fallback")
            file_path = email_sender.fallback_save_report(
                email_body,
                output_dir=config.report_output_dir,
                prefix="logwatch-report"
            )

            if file_path:
                logger.warning(f"Report saved to: {file_path}")
                send_status = "FALLBACK_FILE_SAVED"
            else:
                logger.error("Failed to save report to file")
                send_status = "FALLBACK_FILE_FAILED"

        # ========== Execution Complete ==========
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("=" * 60)
        logger.info(f"Execution completed successfully")
        logger.info(f"  Analysis Status: {analysis_status}")
        logger.info(f"  Send Status: {send_status}")
        logger.info(f"  Total Time: {elapsed:.2f}s")
        logger.info("=" * 60)

        return 0

    except ValueError as e:
        # Configuration error
        logger.error(f"Configuration error: {e}")
        return 2
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        return 130
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    # Add src directory to path for imports
    src_dir = Path(__file__).parent
    sys.path.insert(0, str(src_dir))

    try:
        # Load config first to setup logging
        config = Config()
        setup_logging(config.script_log_file, config.log_level)

        # Run main
        sys.exit(main())

    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)
