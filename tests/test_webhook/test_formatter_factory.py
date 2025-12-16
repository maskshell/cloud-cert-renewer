"""Tests for message formatter factory (Factory Pattern)"""

import unittest

from cloud_cert_renewer.webhook.formatters import (
    GenericMessageFormatter,
    MessageFormatterFactory,
    WeChatWorkMessageFormatter,
)


class TestMessageFormatterFactory(unittest.TestCase):
    """Message formatter factory tests (Factory Pattern)"""

    def setUp(self):
        """Set up test fixtures"""
        # Clear any custom registrations
        MessageFormatterFactory._formatters.clear()

    def tearDown(self):
        """Clean up test fixtures"""
        # Clear any custom registrations
        MessageFormatterFactory._formatters.clear()

    def test_factory_create_generic_formatter(self):
        """Test factory creates generic formatter"""
        formatter = MessageFormatterFactory.create("generic")

        self.assertIsInstance(formatter, GenericMessageFormatter)

    def test_factory_create_wechat_work_formatter(self):
        """Test factory creates WeChat Work formatter"""
        formatter = MessageFormatterFactory.create("wechat_work")

        self.assertIsInstance(formatter, WeChatWorkMessageFormatter)

    def test_factory_case_insensitive(self):
        """Test factory is case insensitive"""
        formatter1 = MessageFormatterFactory.create("GENERIC")
        formatter2 = MessageFormatterFactory.create("generic")

        self.assertIsInstance(formatter1, GenericMessageFormatter)
        self.assertIsInstance(formatter2, GenericMessageFormatter)

    def test_factory_invalid_format_type(self):
        """Test factory raises error for invalid format type"""
        with self.assertRaises(ValueError) as context:
            MessageFormatterFactory.create("invalid_format")

        self.assertIn("Unsupported message format type", str(context.exception))

    def test_factory_register_custom_formatter(self):
        """Test factory can register custom formatter"""

        class CustomFormatter(GenericMessageFormatter):
            """Custom formatter for testing"""

            pass

        MessageFormatterFactory.register_formatter("custom", CustomFormatter)
        formatter = MessageFormatterFactory.create("custom")

        self.assertIsInstance(formatter, CustomFormatter)

    def test_factory_default_formatters_registered(self):
        """Test factory has default formatters registered"""
        formatter1 = MessageFormatterFactory.create("generic")
        formatter2 = MessageFormatterFactory.create("wechat_work")

        self.assertIsInstance(formatter1, GenericMessageFormatter)
        self.assertIsInstance(formatter2, WeChatWorkMessageFormatter)
