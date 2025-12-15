"""Webhook exceptions

Defines webhook-specific exceptions.
"""


class WebhookError(RuntimeError):
    """Base webhook error"""

    pass


class WebhookDeliveryError(WebhookError):
    """Failed to deliver webhook"""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class WebhookConfigError(WebhookError):
    """Invalid webhook configuration"""

    pass
