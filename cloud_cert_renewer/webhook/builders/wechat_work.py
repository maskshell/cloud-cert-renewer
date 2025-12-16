"""WeChat Work message builders

Builds WeChat Work (企业微信) specific message payloads.
"""

from typing import Any

from cloud_cert_renewer.webhook.exceptions import WebhookError


class WeChatWorkTextMessageBuilder:
    """Builder for WeChat Work text messages"""

    MAX_CONTENT_LENGTH = 2048  # Maximum content length in bytes (UTF-8 encoded)

    def __init__(self) -> None:
        """Initialize builder"""
        self._content: str | None = None
        self._mentioned_list: list[str] | None = None
        self._mentioned_mobile_list: list[str] | None = None

    def set_content(self, content: str) -> "WeChatWorkTextMessageBuilder":
        """
        Set message content

        :param content: Message content
        :return: Self for method chaining
        :raises WebhookError: If content exceeds maximum length
        """
        # Validate content length (UTF-8 encoded)
        content_bytes = content.encode("utf-8")
        if len(content_bytes) > self.MAX_CONTENT_LENGTH:
            raise WebhookError(
                f"Content length ({len(content_bytes)} bytes) exceeds maximum "
                f"allowed length ({self.MAX_CONTENT_LENGTH} bytes)"
            )
        self._content = content
        return self

    def set_mentioned_list(self, userids: list[str]) -> "WeChatWorkTextMessageBuilder":
        """
        Set list of userids to @mention

        :param userids: List of userids
        :return: Self for method chaining
        """
        self._mentioned_list = userids
        return self

    def set_mentioned_mobile_list(
        self, mobiles: list[str]
    ) -> "WeChatWorkTextMessageBuilder":
        """
        Set list of mobile numbers to @mention

        :param mobiles: List of mobile numbers
        :return: Self for method chaining
        """
        self._mentioned_mobile_list = mobiles
        return self

    def build(self) -> dict[str, Any]:
        """
        Build WeChat Work text message payload

        :return: Message payload dictionary
        :raises WebhookError: If content is not set
        """
        if self._content is None:
            raise WebhookError("Content is required for WeChat Work text message")

        payload: dict[str, Any] = {
            "msgtype": "text",
            "text": {
                "content": self._content,
            },
        }

        # Add optional fields if set
        if self._mentioned_list is not None:
            payload["text"]["mentioned_list"] = self._mentioned_list

        if self._mentioned_mobile_list is not None:
            payload["text"]["mentioned_mobile_list"] = self._mentioned_mobile_list

        return payload
