"""Webhook notification service

Provides webhook notification functionality for certificate renewal events.
"""

import logging
import threading

from cloud_cert_renewer.webhook.client import WebhookClient
from cloud_cert_renewer.webhook.events import WebhookEvent
from cloud_cert_renewer.webhook.exceptions import (
    WebhookConfigError,
    WebhookDeliveryError,
    WebhookError,
)

logger = logging.getLogger(__name__)

# Export main classes and exceptions
__all__ = [
    "WebhookService",
    "WebhookEvent",
    "WebhookDeliveryError",
    "WebhookError",
    "WebhookConfigError",
]


class WebhookService:
    """Main webhook notification service"""

    def __init__(
        self,
        url: str | None = None,
        timeout: int = 30,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
        enabled_events: set[str] | None = None,
    ) -> None:
        """
        Initialize webhook service

        :param url: Webhook URL
        :param timeout: Request timeout in seconds
        :param retry_attempts: Number of retry attempts
        :param retry_delay: Delay between retries in seconds
        :param enabled_events: Set of event types to send webhooks for
        """
        self.url = url
        self.enabled_events = enabled_events or {
            "renewal_started",
            "renewal_success",
            "renewal_failed",
            "renewal_skipped",
            "batch_completed",
        }

        if self.url:
            self.client = WebhookClient(
                timeout=timeout,
                retry_attempts=retry_attempts,
                retry_delay=retry_delay,
            )
        else:
            self.client = None

    def is_enabled(self, event_type: str) -> bool:
        """
        Check if webhook is enabled for a given event type

        :param event_type: Event type to check
        :return: True if webhook should be sent for this event type
        """
        return bool(self.url and self.client and event_type in self.enabled_events)

    def send_event(self, event: WebhookEvent) -> bool:
        """
        Send webhook event asynchronously

        :param event: Webhook event to send
        :return: True if event was queued for delivery
        """
        if not self.is_enabled(event.event_type):
            logger.debug("Webhook disabled for event type: %s", event.event_type)
            return False

        # Send in a separate thread to avoid blocking the main process
        thread = threading.Thread(
            target=self._send_event_sync,
            args=(event,),
            daemon=True,
        )
        thread.start()

        return True

    def _send_event_sync(self, event: WebhookEvent) -> None:
        """
        Send webhook event synchronously

        :param event: Webhook event to send
        """
        if not self.client or not self.url:
            logger.warning("Webhook client not initialized")
            return

        try:
            payload = event.to_dict()
            logger.debug("Sending webhook event: %s", event.event_type)

            success = self.client.deliver(self.url, payload)

            if success:
                logger.info(
                    "Webhook sent successfully: event_type=%s, event_id=%s",
                    event.event_type,
                    event.event_id,
                )
            else:
                logger.warning(
                    "Failed to send webhook: event_type=%s, event_id=%s",
                    event.event_type,
                    event.event_id,
                )
        except Exception as e:
            # Handle unexpected errors (e.g., serialization errors)
            logger.exception(
                "Unexpected error sending webhook: event_type=%s, "
                "event_id=%s, error=%s",
                event.event_type,
                event.event_id,
                e,
            )
