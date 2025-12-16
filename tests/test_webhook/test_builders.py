"""Tests for webhook message builders"""

import unittest

from cloud_cert_renewer.webhook.builders.wechat_work import (
    WeChatWorkTextMessageBuilder,
)
from cloud_cert_renewer.webhook.exceptions import WebhookError


class TestWeChatWorkTextMessageBuilder(unittest.TestCase):
    """WeChat Work text message builder tests"""

    def setUp(self):
        """Set up test fixtures"""
        self.builder = WeChatWorkTextMessageBuilder()

    def test_build_requires_content(self):
        """Test builder requires content"""
        with self.assertRaises(WebhookError) as context:
            self.builder.build()

        self.assertIn("Content is required", str(context.exception))

    def test_build_creates_correct_format(self):
        """Test builder creates correct WeChat Work format"""
        result = self.builder.set_content("Test message").build()

        self.assertIsInstance(result, dict)
        self.assertEqual(result["msgtype"], "text")
        self.assertIn("text", result)
        self.assertEqual(result["text"]["content"], "Test message")

    def test_build_with_mentioned_list(self):
        """Test builder with mentioned_list"""
        result = (
            self.builder.set_content("Test message")
            .set_mentioned_list(["user1", "user2"])
            .build()
        )

        self.assertEqual(result["text"]["mentioned_list"], ["user1", "user2"])

    def test_build_with_mentioned_mobile_list(self):
        """Test builder with mentioned_mobile_list"""
        result = (
            self.builder.set_content("Test message")
            .set_mentioned_mobile_list(["13800001111", "13800002222"])
            .build()
        )

        self.assertEqual(
            result["text"]["mentioned_mobile_list"],
            ["13800001111", "13800002222"],
        )

    def test_build_with_all_optional_fields(self):
        """Test builder with all optional fields"""
        result = (
            self.builder.set_content("Test message")
            .set_mentioned_list(["user1"])
            .set_mentioned_mobile_list(["13800001111"])
            .build()
        )

        self.assertEqual(result["text"]["content"], "Test message")
        self.assertEqual(result["text"]["mentioned_list"], ["user1"])
        self.assertEqual(result["text"]["mentioned_mobile_list"], ["13800001111"])

    def test_build_content_length_validation(self):
        """Test builder validates content length"""
        # Create content that exceeds 2048 bytes (UTF-8)
        long_content = "a" * 3000  # 3000 characters = 3000 bytes in UTF-8

        with self.assertRaises(WebhookError) as context:
            self.builder.set_content(long_content)

        self.assertIn("exceeds maximum allowed length", str(context.exception))

    def test_build_content_with_unicode(self):
        """Test builder handles Unicode content correctly"""
        unicode_content = "测试消息：证书续期成功 ✅"
        result = self.builder.set_content(unicode_content).build()

        self.assertEqual(result["text"]["content"], unicode_content)
        # Verify UTF-8 encoding length
        content_bytes = unicode_content.encode("utf-8")
        self.assertLessEqual(len(content_bytes), 2048)

    def test_build_method_chaining(self):
        """Test builder supports method chaining"""
        result = (
            self.builder.set_content("Test")
            .set_mentioned_list(["user1"])
            .set_mentioned_mobile_list(["13800001111"])
            .build()
        )

        self.assertIsNotNone(result)
        self.assertEqual(result["text"]["content"], "Test")

    def test_build_max_length_content(self):
        """Test builder accepts content at maximum length"""
        # Create content exactly at 2048 bytes
        max_content = "a" * 2048
        result = self.builder.set_content(max_content).build()

        self.assertEqual(result["text"]["content"], max_content)
