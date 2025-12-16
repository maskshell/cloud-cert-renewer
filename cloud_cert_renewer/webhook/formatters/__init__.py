"""Webhook message formatters

Provides message formatting functionality for different webhook formats.
"""

from cloud_cert_renewer.webhook.formatters.base import MessageFormatter
from cloud_cert_renewer.webhook.formatters.generic import GenericMessageFormatter
from cloud_cert_renewer.webhook.formatters.wechat_work import (
    WeChatWorkMessageFormatter,
)

__all__ = [
    "MessageFormatter",
    "GenericMessageFormatter",
    "WeChatWorkMessageFormatter",
    "MessageFormatterFactory",
]


class MessageFormatterFactory:
    """Message formatter factory"""

    _formatters: dict[str, type[MessageFormatter]] = {}

    @classmethod
    def _register_default_formatters(cls) -> None:
        """Register default formatters"""
        from cloud_cert_renewer.webhook.formatters.generic import (
            GenericMessageFormatter,
        )
        from cloud_cert_renewer.webhook.formatters.wechat_work import (
            WeChatWorkMessageFormatter,
        )

        defaults: dict[str, type[MessageFormatter]] = {
            "generic": GenericMessageFormatter,
            "wechat_work": WeChatWorkMessageFormatter,
        }

        # Merge defaults without overwriting any formatters already registered
        for name, formatter in defaults.items():
            cls._formatters.setdefault(name, formatter)

    @classmethod
    def create(cls, format_type: str) -> MessageFormatter:
        """
        Create message formatter

        :param format_type: Format type (generic, wechat_work, etc.)
        :return: MessageFormatter instance
        :raises ValueError: When format type is not supported
        """
        cls._register_default_formatters()
        format_type = format_type.lower()
        formatter_class = cls._formatters.get(format_type)
        if not formatter_class:
            supported = ", ".join(cls._formatters.keys())
            raise ValueError(
                f"Unsupported message format type: {format_type}, "
                f"supported: {supported}"
            )
        return formatter_class()

    @classmethod
    def register_formatter(
        cls, format_type: str, formatter_class: type[MessageFormatter]
    ) -> None:
        """
        Register a custom formatter

        :param format_type: Format type identifier
        :param formatter_class: Formatter class
        """
        cls._formatters[format_type.lower()] = formatter_class
