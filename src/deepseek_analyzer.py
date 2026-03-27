"""
DeepSeek API analyzer module.
Sends logwatch output to DeepSeek for analysis and receives structured JSON response.
"""
import requests
import json
import logging
import time
import re
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class DeepSeekAnalyzer:
    """Analyzes logwatch output using DeepSeek API."""

    # DeepSeek API endpoint
    API_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
    MODEL = "deepseek-chat"

    def __init__(
        self,
        api_key: str,
        max_retries: int = 3,
        timeout: int = 30,
        retry_backoff: float = 2.0,
        max_input_chars: int = 50000,
    ):
        """
        Initialize DeepSeek analyzer.

        Args:
            api_key: DeepSeek API key
            max_retries: Maximum number of retries on failure
            timeout: Request timeout in seconds
            retry_backoff: Backoff multiplier for retries (exponential)
            max_input_chars: Maximum log input size before compaction
        """
        self.api_key = api_key
        self.max_retries = max_retries
        self.timeout = timeout
        self.retry_backoff = retry_backoff
        self.max_input_chars = max_input_chars

    def analyze(self, logwatch_output: str) -> Optional[Dict[str, Any]]:
        """
        Analyze logwatch output and return structured JSON response.
        Returns None on failure (fallback to raw logwatch output in main.py).

        Args:
            logwatch_output: Plain text output from logwatch

        Returns:
            Dictionary with analysis result, or None if analysis failed
        """
        if not logwatch_output or not logwatch_output.strip():
            logger.warning("Empty logwatch output provided for analysis")
            return None

        compacted_output = self._compact_logwatch_output(logwatch_output)
        prompt = self._build_analysis_prompt(compacted_output)

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Calling DeepSeek API (attempt {attempt + 1}/{self.max_retries})")

                response = self._call_api(prompt)

                if response is None:
                    if attempt < self.max_retries - 1:
                        wait_time = self._calculate_backoff(attempt)
                        logger.warning(f"API call failed, retrying in {wait_time}s...")
                        time.sleep(wait_time)
                    continue

                # Parse and validate response
                analysis_result = self._parse_response(response)
                if analysis_result:
                    logger.info("DeepSeek analysis completed successfully")
                    return analysis_result

            except Exception as e:
                logger.error(f"Error during analysis (attempt {attempt + 1}): {e}", exc_info=True)
                if attempt < self.max_retries - 1:
                    wait_time = self._calculate_backoff(attempt)
                    time.sleep(wait_time)

        logger.error(f"DeepSeek API failed after {self.max_retries} attempts")
        return None  # Trigger fallback in main.py

    def _call_api(self, prompt: str) -> Optional[str]:
        """
        Make HTTP request to DeepSeek API.

        Args:
            prompt: Analysis prompt

        Returns:
            Response text, or None on failure
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a system log analyzer. Analyze the provided logwatch output and respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0,  # Deterministic output for analysis
            "max_tokens": 2000
        }

        try:
            response = requests.post(
                self.API_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
            elif response.status_code == 429:
                logger.warning("DeepSeek API rate limit exceeded")
                return None
            elif response.status_code == 401:
                logger.error("DeepSeek API authentication failed (check API key)")
                return None
            else:
                logger.error(f"DeepSeek API error {response.status_code}: {response.text}")
                return None

        except requests.Timeout:
            logger.error(f"DeepSeek API timeout after {self.timeout}s")
            return None
        except requests.RequestException as e:
            logger.error(f"DeepSeek API request failed: {e}")
            return None

    def _parse_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """
        Parse and validate API response.

        Args:
            response_text: Raw response from API

        Returns:
            Parsed JSON dictionary, or None if parsing failed
        """
        try:
            # Try to extract JSON from response (API might include extra text)
            response_text = response_text.strip()

            # Find JSON structure
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx == -1 or end_idx <= start_idx:
                logger.error("No JSON structure found in API response")
                return None

            json_str = response_text[start_idx:end_idx]
            parsed = json.loads(json_str)

            # Validate expected keys
            if not isinstance(parsed, dict):
                logger.error("API response is not a JSON object")
                return None

            logger.debug(f"Successfully parsed API response with keys: {parsed.keys()}")
            return parsed

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response text: {response_text[:200]}...")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}", exc_info=True)
            return None

    def _build_analysis_prompt(self, logwatch_output: str) -> str:
        """
        Build analysis prompt for DeepSeek.

        Args:
            logwatch_output: Plain text logwatch output

        Returns:
            Formatted prompt
        """
        prompt = f"""Analyze the following system log summary and provide structured insights:

{logwatch_output}

Please analyze and respond with ONLY valid JSON (no additional text) in this format:
{{
  "critical_issues": ["List of critical errors or failures"],
  "security_alerts": ["List of security-related events (failed logins, unauthorized access, etc.)"],
  "performance_issues": ["List of performance problems or resource warnings"],
  "important_warnings": ["List of important warnings"],
  "recommendations": ["List of recommended actions"],
  "summary": "One-sentence summary of the overall system health"
}}

Return empty arrays if no items in that category."""

        return prompt

    def _compact_logwatch_output(self, logwatch_output: str) -> str:
        """
        Compact large logwatch output to avoid model context overflow.

        Strategy:
        1) Keep lines that look important (errors/security/perf signals)
        2) Include small head/tail slices for context
        3) Enforce hard character cap
        """
        if len(logwatch_output) <= self.max_input_chars:
            return logwatch_output

        original_len = len(logwatch_output)
        lines = logwatch_output.splitlines()

        important_pattern = re.compile(
            r"error|warn|fail|denied|timeout|critical|panic|segfault|"
            r"unauthor|invalid|refused|oom|killed process|attack|sudo|sshd|ufw",
            re.IGNORECASE,
        )

        important_lines = [line for line in lines if important_pattern.search(line)]

        # Budgets for each section
        hard_cap = max(self.max_input_chars, 1000)
        important_budget = int(hard_cap * 0.7)
        edge_budget_each = int(hard_cap * 0.15)

        important_text = "\n".join(important_lines)
        if len(important_text) > important_budget:
            important_text = important_text[:important_budget]

        head = logwatch_output[:edge_budget_each]
        tail = logwatch_output[-edge_budget_each:] if len(logwatch_output) > edge_budget_each else ""

        compacted = (
            "[TRUNCATED LOGWATCH OUTPUT]\n"
            f"Original size: {original_len} chars\n"
            f"Compacted size target: <= {hard_cap} chars\n\n"
            "=== IMPORTANT LINES (error/security/perf related) ===\n"
            f"{important_text}\n\n"
            "=== BEGINNING SAMPLE ===\n"
            f"{head}\n\n"
            "=== ENDING SAMPLE ===\n"
            f"{tail}\n"
        )

        if len(compacted) > hard_cap:
            compacted = compacted[:hard_cap]

        logger.warning(
            "Compacted logwatch output for DeepSeek context limit: "
            f"{original_len} -> {len(compacted)} chars"
        )
        return compacted

    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff wait time.

        Args:
            attempt: Current attempt number (0-indexed)

        Returns:
            Wait time in seconds
        """
        return (self.retry_backoff ** attempt)
