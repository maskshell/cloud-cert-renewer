"""Tests for webhook message formatters (Strategy Pattern)"""

import unittest
from datetime import datetime, timezone

from cloud_cert_renewer.webhook.events import (
    EventCertificate,
    EventMetadata,
    EventResult,
    EventSource,
    EventTarget,
    WebhookEvent,
)
from cloud_cert_renewer.webhook.formatters.generic import GenericMessageFormatter
from cloud_cert_renewer.webhook.formatters.wechat_work import (
    WeChatWorkMessageFormatter,
)


class TestGenericMessageFormatter(unittest.TestCase):
    """Generic message formatter tests (Strategy Pattern)"""

    def setUp(self):
        """Set up test fixtures"""
        self.formatter = GenericMessageFormatter()

    def test_format_returns_event_dict(self):
        """Test formatter returns event.to_dict()"""
        event = WebhookEvent(
            event_type="renewal_success",
            source=EventSource(
                service_type="cdn",
                cloud_provider="alibaba",
                region="cn-hangzhou",
            ),
            target=EventTarget(domain_names=["example.com"]),
        )

        result = self.formatter.format(event)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["event_type"], "renewal_success")
        self.assertEqual(result["source"]["service_type"], "cdn")
        self.assertEqual(result["target"]["domain_names"], ["example.com"])

    def test_format_preserves_all_event_fields(self):
        """Test formatter preserves all event fields"""
        event = WebhookEvent(
            event_type="renewal_failed",
            source=EventSource(
                service_type="lb",
                cloud_provider="alibaba",
                region="cn-beijing",
            ),
            target=EventTarget(
                instance_ids=["lb-123"],
                listener_port=443,
            ),
            certificate=EventCertificate(
                fingerprint="abc123",
                not_after=datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
                issuer="Let's Encrypt",
            ),
            result=EventResult(
                status="failure",
                message="Certificate renewal failed",
                error_code="ERR001",
                error_details="Connection timeout",
            ),
            metadata=EventMetadata(
                version="1.0.0",
                execution_time_ms=5000,
                dry_run=True,
            ),
        )

        result = self.formatter.format(event)

        self.assertEqual(result["event_type"], "renewal_failed")
        self.assertEqual(result["source"]["service_type"], "lb")
        self.assertEqual(result["target"]["instance_ids"], ["lb-123"])
        self.assertIn("certificate", result)
        self.assertIn("result", result)
        self.assertIn("metadata", result)


class TestWeChatWorkMessageFormatter(unittest.TestCase):
    """WeChat Work message formatter tests (Strategy Pattern)"""

    def setUp(self):
        """Set up test fixtures"""
        self.formatter = WeChatWorkMessageFormatter()

    def test_format_returns_wechat_work_format(self):
        """Test formatter returns WeChat Work format"""
        event = WebhookEvent(
            event_type="renewal_success",
            source=EventSource(
                service_type="cdn",
                cloud_provider="alibaba",
                region="cn-hangzhou",
            ),
            target=EventTarget(domain_names=["example.com"]),
        )

        result = self.formatter.format(event)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["msgtype"], "text")
        self.assertIn("text", result)
        self.assertIn("content", result["text"])
        self.assertIsInstance(result["text"]["content"], str)

    def test_format_includes_event_information(self):
        """Test formatter includes event information in content"""
        event = WebhookEvent(
            event_type="renewal_success",
            source=EventSource(
                service_type="cdn",
                cloud_provider="alibaba",
                region="cn-hangzhou",
            ),
            target=EventTarget(domain_names=["example.com"]),
        )

        result = self.formatter.format(event)
        content = result["text"]["content"]

        self.assertIn("证书续期成功", content)
        self.assertIn("CDN", content)
        self.assertIn("example.com", content)

    def test_format_includes_certificate_info(self):
        """Test formatter includes certificate information"""
        event = WebhookEvent(
            event_type="renewal_success",
            source=EventSource(
                service_type="cdn",
                cloud_provider="alibaba",
                region="cn-hangzhou",
            ),
            target=EventTarget(domain_names=["example.com"]),
            certificate=EventCertificate(
                not_after=datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
                issuer="Let's Encrypt",
            ),
        )

        result = self.formatter.format(event)
        content = result["text"]["content"]

        self.assertIn("证书到期时间", content)
        self.assertIn("Let's Encrypt", content)

    def test_format_includes_error_info(self):
        """Test formatter includes error information"""
        event = WebhookEvent(
            event_type="renewal_failed",
            source=EventSource(
                service_type="cdn",
                cloud_provider="alibaba",
                region="cn-hangzhou",
            ),
            target=EventTarget(domain_names=["example.com"]),
            result=EventResult(
                status="failure",
                message="Certificate renewal failed",
                error_code="ERR001",
                error_details="Connection timeout",
            ),
        )

        result = self.formatter.format(event)
        content = result["text"]["content"]

        self.assertIn("证书续期失败", content)
        self.assertIn("失败", content)
        self.assertIn("Certificate renewal failed", content)
        self.assertIn("ERR001", content)

    def test_format_content_length_within_limit(self):
        """Test formatter content length is within WeChat Work limit"""
        event = WebhookEvent(
            event_type="batch_completed",
            source=EventSource(
                service_type="cdn",
                cloud_provider="alibaba",
                region="cn-hangzhou",
            ),
            target=EventTarget(domain_names=["example.com"]),
            metadata=EventMetadata(
                version="1.0.0",
                total_resources=100,
                successful_resources=95,
                failed_resources=5,
            ),
        )

        result = self.formatter.format(event)
        content = result["text"]["content"]
        content_bytes = content.encode("utf-8")

        # WeChat Work text message max length is 2048 bytes
        self.assertLessEqual(len(content_bytes), 2048)
