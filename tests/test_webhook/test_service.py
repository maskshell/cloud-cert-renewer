"""Tests for webhook service"""

from unittest.mock import MagicMock, patch

from cloud_cert_renewer.webhook import WebhookService
from cloud_cert_renewer.webhook.events import (
    EventSource,
    EventTarget,
    WebhookEvent,
)


class TestWebhookService:
    """Test WebhookService"""

    def test_service_initialization_with_url(self):
        """Test WebhookService initialization with URL"""
        service = WebhookService(
            url="https://example.com/webhook",
            timeout=60,
            retry_attempts=5,
            retry_delay=2.0,
            enabled_events={"renewal_success", "renewal_failed"},
        )

        assert service.url == "https://example.com/webhook"
        assert service.enabled_events == {"renewal_success", "renewal_failed"}
        assert service.client is not None
        # Verify client was initialized with correct parameters
        assert service.client.timeout == 60
        assert service.client.retry_attempts == 5
        assert service.client.retry_delay == 2.0

    def test_service_initialization_without_url(self):
        """Test WebhookService initialization without URL"""
        service = WebhookService()

        assert service.url is None
        assert service.client is None
        assert service.enabled_events == {
            "renewal_started",
            "renewal_success",
            "renewal_failed",
            "renewal_skipped",
            "batch_completed",
        }
        # Default formatter should be generic
        from cloud_cert_renewer.webhook.formatters.generic import (
            GenericMessageFormatter,
        )

        assert isinstance(service.formatter, GenericMessageFormatter)

    def test_is_enabled_with_url_and_event(self):
        """Test is_enabled with URL and matching event"""
        service = WebhookService(
            url="https://example.com/webhook", enabled_events={"renewal_success"}
        )

        assert service.is_enabled("renewal_success") is True
        assert service.is_enabled("renewal_failed") is False

    def test_is_enabled_without_url(self):
        """Test is_enabled without URL"""
        service = WebhookService()

        assert service.is_enabled("renewal_success") is False
        assert service.is_enabled("renewal_failed") is False

    def test_is_enabled_with_default_events(self):
        """Test is_enabled with default event set"""
        service = WebhookService(url="https://example.com/webhook")

        # All default events should be enabled
        assert service.is_enabled("renewal_started") is True
        assert service.is_enabled("renewal_success") is True
        assert service.is_enabled("renewal_failed") is True
        assert service.is_enabled("renewal_skipped") is True
        assert service.is_enabled("batch_completed") is True

        # Non-default events should be disabled
        assert service.is_enabled("custom_event") is False

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    @patch("threading.Thread")
    def test_send_event_async(self, mock_thread, mock_client_class):
        """Test that send_event sends asynchronously"""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        service = WebhookService(
            url="https://example.com/webhook", enabled_events={"renewal_success"}
        )

        event = WebhookEvent(
            event_type="renewal_success",
            source=EventSource(
                service_type="cdn",
                cloud_provider="alibaba",
                region="cn-hangzhou",
            ),
            target=EventTarget(domain_names=["example.com"]),
        )

        result = service.send_event(event)

        assert result is True
        mock_thread.assert_called_once()

        # Check that thread was created with correct arguments
        thread_args = mock_thread.call_args
        assert thread_args[1]["target"] == service._send_event_sync
        assert thread_args[1]["args"] == (event,)
        assert thread_args[1]["daemon"] is True

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    def test_send_event_sync_success(self, mock_client_class):
        """Test synchronous event sending success"""
        mock_client = MagicMock()
        mock_client.deliver.return_value = True
        mock_client_class.return_value = mock_client

        service = WebhookService(
            url="https://example.com/webhook", enabled_events={"renewal_success"}
        )

        event = WebhookEvent(
            event_type="renewal_success",
            source=EventSource(
                service_type="cdn",
                cloud_provider="alibaba",
                region="cn-hangzhou",
            ),
            target=EventTarget(domain_names=["example.com"]),
        )

        service._send_event_sync(event)

        # Verify client was called correctly
        mock_client.deliver.assert_called_once()
        call_args = mock_client.deliver.call_args
        assert call_args[0][0] == "https://example.com/webhook"

        # Check payload structure
        payload = call_args[0][1]
        assert payload["event_type"] == "renewal_success"
        assert payload["source"]["service_type"] == "cdn"
        assert payload["target"]["domain_names"] == ["example.com"]

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    @patch("cloud_cert_renewer.webhook.logger")
    def test_send_event_sync_client_failure(self, mock_logger, mock_client_class):
        """Test synchronous event sending with client failure"""
        mock_client = MagicMock()
        mock_client.deliver.return_value = False
        mock_client_class.return_value = mock_client

        service = WebhookService(
            url="https://example.com/webhook", enabled_events={"renewal_success"}
        )

        event = WebhookEvent(
            event_type="renewal_success",
            source=EventSource(
                service_type="cdn",
                cloud_provider="alibaba",
                region="cn-hangzhou",
            ),
            target=EventTarget(domain_names=["example.com"]),
        )

        service._send_event_sync(event)

        # Verify warning was logged
        assert mock_logger.warning.called

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    @patch("cloud_cert_renewer.webhook.logger")
    def test_send_event_sync_delivery_error(self, mock_logger, mock_client_class):
        """Test synchronous event sending with delivery error"""
        # deliver() now returns False instead of raising exception
        mock_client = MagicMock()
        mock_client.deliver.return_value = False
        mock_client_class.return_value = mock_client

        service = WebhookService(
            url="https://example.com/webhook", enabled_events={"renewal_success"}
        )

        event = WebhookEvent(
            event_type="renewal_success",
            source=EventSource(
                service_type="cdn",
                cloud_provider="alibaba",
                region="cn-hangzhou",
            ),
            target=EventTarget(domain_names=["example.com"]),
        )

        service._send_event_sync(event)

        # Verify warning was logged (for failed delivery)
        mock_logger.warning.assert_called()

    def test_send_event_disabled(self):
        """Test send_event when webhook is disabled"""
        service = WebhookService()  # No URL configured

        event = WebhookEvent(
            event_type="renewal_success",
            source=EventSource(
                service_type="cdn",
                cloud_provider="alibaba",
                region="cn-hangzhou",
            ),
            target=EventTarget(domain_names=["example.com"]),
        )

        result = service.send_event(event)

        assert result is False

    def test_send_event_event_type_disabled(self):
        """Test send_event when event type is disabled"""
        service = WebhookService(
            url="https://example.com/webhook",
            enabled_events={"renewal_success"},  # Only renewal_success enabled
        )

        event = WebhookEvent(
            event_type="renewal_failed",  # Different event type
            source=EventSource(
                service_type="cdn", cloud_provider="alibaba", region="cn-hangzhou"
            ),
            target=EventTarget(domain_names=["example.com"]),
        )

        result = service.send_event(event)

        assert result is False

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    @patch("cloud_cert_renewer.webhook.logger")
    def test_send_event_unexpected_error(self, mock_logger, mock_client_class):
        """Test send_event with unexpected error (e.g., serialization error)"""
        # Simulate an unexpected error during event serialization or delivery
        mock_client = MagicMock()
        # Simulate error during to_dict() or deliver() call
        mock_client.deliver.side_effect = Exception("Unexpected error")
        mock_client_class.return_value = mock_client

        service = WebhookService(
            url="https://example.com/webhook", enabled_events={"renewal_success"}
        )

        event = WebhookEvent(
            event_type="renewal_success",
            source=EventSource(
                service_type="cdn",
                cloud_provider="alibaba",
                region="cn-hangzhou",
            ),
            target=EventTarget(domain_names=["example.com"]),
        )

        service._send_event_sync(event)

        # Verify exception was logged (for unexpected errors)
        mock_logger.exception.assert_called()

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    @patch("cloud_cert_renewer.webhook.logger")
    def test_send_event_no_client(self, mock_logger, mock_client_class):
        """Test send_event when client is not initialized"""
        service = WebhookService()  # No URL = no client
        # Manually set URL but keep client as None
        service.url = "https://example.com/webhook"

        event = WebhookEvent(
            event_type="renewal_success",
            source=EventSource(
                service_type="cdn",
                cloud_provider="alibaba",
                region="cn-hangzhou",
            ),
            target=EventTarget(domain_names=["example.com"]),
        )

        service._send_event_sync(event)

        # Verify warning was logged
        mock_logger.warning.assert_called_with("Webhook client not initialized")

    def test_service_initialization_with_message_format(self):
        """Test WebhookService initialization with message_format"""
        from cloud_cert_renewer.webhook.formatters.generic import (
            GenericMessageFormatter,
        )
        from cloud_cert_renewer.webhook.formatters.wechat_work import (
            WeChatWorkMessageFormatter,
        )

        # Test generic format (default)
        service1 = WebhookService(
            url="https://example.com/webhook", message_format="generic"
        )
        assert isinstance(service1.formatter, GenericMessageFormatter)

        # Test WeChat Work format
        service2 = WebhookService(
            url="https://example.com/webhook", message_format="wechat_work"
        )
        assert isinstance(service2.formatter, WeChatWorkMessageFormatter)

        # Test invalid format (should fallback to generic)
        service3 = WebhookService(
            url="https://example.com/webhook", message_format="invalid"
        )
        assert isinstance(service3.formatter, GenericMessageFormatter)

    @patch("cloud_cert_renewer.webhook.WebhookClient")
    def test_send_event_uses_formatter(self, mock_client_class):
        """Test that send_event uses configured formatter"""
        from cloud_cert_renewer.webhook.formatters.wechat_work import (
            WeChatWorkMessageFormatter,
        )

        mock_client = MagicMock()
        mock_client.deliver.return_value = True
        mock_client_class.return_value = mock_client

        service = WebhookService(
            url="https://example.com/webhook",
            enabled_events={"renewal_success"},
            message_format="wechat_work",
        )

        assert isinstance(service.formatter, WeChatWorkMessageFormatter)

        event = WebhookEvent(
            event_type="renewal_success",
            source=EventSource(
                service_type="cdn",
                cloud_provider="alibaba",
                region="cn-hangzhou",
            ),
            target=EventTarget(domain_names=["example.com"]),
        )

        service._send_event_sync(event)

        # Verify client was called
        mock_client.deliver.assert_called_once()
        call_args = mock_client.deliver.call_args
        payload = call_args[0][1]

        # Verify payload is in WeChat Work format
        assert payload["msgtype"] == "text"
        assert "text" in payload
        assert "content" in payload["text"]
