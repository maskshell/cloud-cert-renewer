"""Base message formatter interface

Defines the contract for all message formatters using Strategy Pattern.
"""

from abc import ABC, abstractmethod
from typing import Any

from cloud_cert_renewer.webhook.events import WebhookEvent


class MessageFormatter(ABC):
    """Abstract base class for message formatters (Strategy Pattern)"""

    @abstractmethod
    def format(self, event: WebhookEvent) -> dict[str, Any]:
        """
        Format webhook event into message payload

        :param event: Webhook event to format
        :return: Formatted message payload as dictionary
        """
        pass
