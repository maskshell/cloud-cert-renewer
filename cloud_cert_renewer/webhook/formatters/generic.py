"""Generic message formatter

Formats webhook events using the generic format (existing behavior).
Suitable for webhooks with no specific format requirements or arbitrary JSON.
"""

from typing import Any

from cloud_cert_renewer.webhook.events import WebhookEvent
from cloud_cert_renewer.webhook.formatters.base import MessageFormatter


class GenericMessageFormatter(MessageFormatter):
    """Generic message formatter (default format)

    Returns the event as-is using to_dict() method.
    Suitable for:
    - Webhooks with no specific format requirements
    - Webhooks that require JSON but have no specific JSON structure requirements
    - IM platforms like Slack, Discord, etc. (future extensions)
    """

    def format(self, event: WebhookEvent) -> dict[str, Any]:
        """
        Format webhook event using generic format

        :param event: Webhook event to format
        :return: Event dictionary (existing behavior)
        """
        return event.to_dict()
