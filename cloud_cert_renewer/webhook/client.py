"""Webhook HTTP client

Handles HTTP delivery of webhooks with retry logic.
"""

import json
import logging
import time
from typing import Any

import urllib3
from urllib3 import HTTPResponse

from cloud_cert_renewer import __version__
from cloud_cert_renewer.webhook.exceptions import WebhookDeliveryError

logger = logging.getLogger(__name__)


class WebhookClient:
    """HTTP client for webhook delivery with retry logic"""

    def __init__(
        self, timeout: int = 30, retry_attempts: int = 3, retry_delay: float = 1.0
    ) -> None:
        """
        Initialize webhook client

        :param timeout: Request timeout in seconds
        :param retry_attempts: Number of retry attempts
        :param retry_delay: Initial delay between retries in seconds
            (exponential backoff)
        """
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        # Create HTTP client with appropriate pool settings
        self.http = urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=timeout, read=timeout),
            retries=urllib3.Retry(
                total=0,  # We handle retries ourselves
                redirect=5,
                backoff_factor=0,
            ),
            headers={
                "Content-Type": "application/json",
                "User-Agent": f"cloud-cert-renewer/{__version__}",
            },
        )

    def deliver(self, url: str, payload: dict[str, Any]) -> bool:
        """
        Deliver webhook with retries and error handling

        :param url: Webhook URL
        :param payload: JSON payload to send
        :return: True if delivery succeeded, False otherwise
        """
        json_data = json.dumps(payload, default=str)
        encoded_data = json_data.encode("utf-8")

        last_exception = None

        for attempt in range(self.retry_attempts + 1):
            if attempt > 0:
                delay = self.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                logger.info(
                    "Webhook delivery attempt %d/%d failed, retrying in %.2fs",
                    attempt + 1,
                    self.retry_attempts + 1,
                    delay,
                )
                time.sleep(delay)

            try:
                logger.debug(
                    "Sending webhook to %s (attempt %d/%d)",
                    url,
                    attempt + 1,
                    self.retry_attempts + 1,
                )

                response: HTTPResponse = self.http.request(
                    "POST",
                    url,
                    body=encoded_data,
                    headers={"Content-Length": str(len(encoded_data))},
                )

                response_text = response.data.decode("utf-8", errors="replace")

                # Consider 2xx status codes as success,
                # but check response body for errors
                if 200 <= response.status < 300:
                    # Check if response body contains error information
                    # Some webhook services (e.g., WeChat Work) return HTTP 200
                    # but include error codes in the response body
                    error_detected = False
                    error_message = None

                    try:
                        # Try to parse response as JSON
                        response_json = json.loads(response_text)
                        # Check for common error fields in response
                        if isinstance(response_json, dict):
                            # WeChat Work uses "errcode" field (0 means success)
                            if "errcode" in response_json:
                                errcode = response_json.get("errcode", 0)
                                if errcode != 0:
                                    error_detected = True
                                    errmsg = response_json.get(
                                        "errmsg", "Unknown error"
                                    )
                                    error_message = (
                                        f"errcode={errcode}, errmsg={errmsg}"
                                    )
                            # Some services use "error" or "status" fields
                            elif "error" in response_json and response_json["error"]:
                                error_detected = True
                                error_message = f"error={response_json['error']}"
                            elif (
                                "status" in response_json
                                and response_json["status"] != "success"
                                and response_json["status"] != "ok"
                            ):
                                error_detected = True
                                error_message = f"status={response_json['status']}"
                    except (json.JSONDecodeError, ValueError):
                        # Response is not JSON, or parsing failed
                        # If response is not empty and not a simple success message,
                        # we might want to log it but still consider it success
                        # (some services return plain text "OK" or similar)
                        pass

                    if error_detected:
                        logger.warning(
                            "Webhook delivery failed: status=%d, url=%s, response=%s",
                            response.status,
                            url,
                            error_message or response_text[:200],
                        )
                        error_detail = error_message or response_text[:200]
                        last_exception = WebhookDeliveryError(
                            f"HTTP {response.status}: {error_detail}",
                            status_code=response.status,
                            response=response_text,
                        )
                        # Continue to retry logic
                    else:
                        logger.info(
                            "Webhook delivered successfully: status=%d, url=%s",
                            response.status,
                            url,
                        )
                        return True
                else:
                    logger.warning(
                        "Webhook delivery failed: status=%d, url=%s, response=%s",
                        response.status,
                        url,
                        response_text[:200],
                    )
                    last_exception = WebhookDeliveryError(
                        f"HTTP {response.status}: {response_text[:200]}",
                        status_code=response.status,
                        response=response_text,
                    )

            except urllib3.exceptions.TimeoutError as e:
                logger.warning("Webhook delivery timeout: url=%s", url)
                last_exception = WebhookDeliveryError(f"Timeout: {e}")

            except urllib3.exceptions.HTTPError as e:
                logger.warning("Webhook delivery HTTP error: url=%s, error=%s", url, e)
                last_exception = WebhookDeliveryError(f"HTTP error: {e}")

            except Exception as e:
                logger.exception(
                    "Webhook delivery unexpected error: url=%s, error=%s", url, e
                )
                last_exception = WebhookDeliveryError(f"Unexpected error: {e}")

        # All attempts failed
        error_msg = str(last_exception) if last_exception else "Unknown error"
        logger.error(
            "Webhook delivery failed after %d attempts: url=%s, last_error=%s",
            self.retry_attempts + 1,
            url,
            error_msg,
        )

        # Return False instead of raising exception
        # Webhook delivery failure is an expected business scenario,
        # not an exceptional case that requires exception handling
        return False
