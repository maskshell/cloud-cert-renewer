"""Tests for webhook client"""

import json
from unittest.mock import MagicMock, patch

import urllib3

from cloud_cert_renewer.webhook.client import WebhookClient


class TestWebhookClient:
    """Test WebhookClient"""

    def test_client_initialization(self):
        """Test WebhookClient initialization"""
        client = WebhookClient(timeout=60, retry_attempts=5, retry_delay=2.0)
        assert client.timeout == 60
        assert client.retry_attempts == 5
        assert client.retry_delay == 2.0

    @patch("urllib3.PoolManager.request")
    def test_deliver_success(self, mock_request):
        """Test successful webhook delivery"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.data = b'{"status": "ok"}'
        mock_request.return_value = mock_response

        client = WebhookClient()
        payload = {"event_type": "test", "data": "test data"}

        result = client.deliver("https://example.com/webhook", payload)

        assert result is True
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        assert call_args[0][0] == "POST"
        assert call_args[0][1] == "https://example.com/webhook"
        assert json.loads(call_args[1]["body"]) == payload

    @patch("urllib3.PoolManager.request")
    def test_deliver_2xx_success(self, mock_request):
        """Test webhook delivery with various 2xx status codes"""
        for status_code in [200, 201, 204, 299]:
            mock_request.reset_mock()
            mock_response = MagicMock()
            mock_response.status = status_code
            mock_response.data = b"OK"
            mock_request.return_value = mock_response

            client = WebhookClient()
            payload = {"test": "data"}

            result = client.deliver("https://example.com/webhook", payload)

            assert result is True, f"Status {status_code} should be considered success"

    @patch("urllib3.PoolManager.request")
    def test_deliver_failure_non_2xx(self, mock_request):
        """Test webhook delivery with non-2xx status codes"""
        mock_response = MagicMock()
        mock_response.status = 400
        mock_response.data = b"Bad Request"
        mock_request.return_value = mock_response

        # Use retry_attempts=0 to test single attempt behavior
        # range(0 + 1) = range(1) means 1 attempt total
        client = WebhookClient(retry_attempts=0)
        payload = {"test": "data"}

        result = client.deliver("https://example.com/webhook", payload)

        assert result is False
        # With retry_attempts=0, should only attempt once
        assert mock_request.call_count == 1

    @patch("urllib3.PoolManager.request")
    def test_deliver_with_retry(self, mock_request):
        """Test webhook delivery with retry logic"""
        # First attempt fails, second succeeds
        mock_response_fail = MagicMock()
        mock_response_fail.status = 500
        mock_response_fail.data = b"Internal Server Error"

        mock_response_success = MagicMock()
        mock_response_success.status = 200
        mock_response_success.data = b"OK"

        mock_request.side_effect = [mock_response_fail, mock_response_success]

        # Small delay for tests
        client = WebhookClient(retry_attempts=2, retry_delay=0.01)
        payload = {"test": "data"}

        result = client.deliver("https://example.com/webhook", payload)

        assert result is True
        assert mock_request.call_count == 2

    @patch("urllib3.PoolManager.request")
    @patch("time.sleep")  # Mock sleep to speed up tests
    def test_deliver_max_retries_exceeded(self, mock_sleep, mock_request):
        """Test webhook delivery when max retries are exceeded"""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.data = b"Internal Server Error"
        mock_request.return_value = mock_response

        client = WebhookClient(retry_attempts=2, retry_delay=0.01)
        payload = {"test": "data"}

        result = client.deliver("https://example.com/webhook", payload)

        assert result is False
        assert mock_request.call_count == 3  # Initial + 2 retries
        assert mock_sleep.call_count == 2  # 2 retries = 2 sleeps

    @patch("urllib3.PoolManager.request")
    def test_deliver_timeout_error(self, mock_request):
        """Test webhook delivery with timeout error"""
        mock_request.side_effect = urllib3.exceptions.TimeoutError("Request timeout")

        client = WebhookClient(retry_attempts=1, retry_delay=0.01)
        payload = {"test": "data"}

        # deliver() returns False on failure, doesn't raise exception
        result = client.deliver("https://example.com/webhook", payload)

        assert result is False
        # Should attempt initial + 1 retry = 2 attempts total
        assert mock_request.call_count == 2

    @patch("urllib3.PoolManager.request")
    def test_deliver_http_error(self, mock_request):
        """Test webhook delivery with HTTP error"""
        mock_request.side_effect = urllib3.exceptions.HTTPError("HTTP error")

        client = WebhookClient(retry_attempts=1, retry_delay=0.01)
        payload = {"test": "data"}

        # deliver() returns False on failure, doesn't raise exception
        result = client.deliver("https://example.com/webhook", payload)

        assert result is False
        # Should attempt initial + 1 retry = 2 attempts total
        assert mock_request.call_count == 2

    @patch("urllib3.PoolManager.request")
    def test_deliver_exponential_backoff(self, mock_request):
        """Test exponential backoff in retries"""
        mock_response = MagicMock()
        mock_response.status = 500
        mock_response.data = b"Internal Server Error"
        mock_request.return_value = mock_response

        client = WebhookClient(retry_attempts=3, retry_delay=0.1)
        payload = {"test": "data"}

        with patch("time.sleep") as mock_sleep:
            result = client.deliver("https://example.com/webhook", payload)

            assert result is False
            assert mock_request.call_count == 4  # Initial + 3 retries

            # Check exponential backoff: 0.1, 0.2, 0.4
            expected_calls = [0.1, 0.2, 0.4]
            actual_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert actual_calls == expected_calls

    @patch("urllib3.PoolManager.request")
    def test_deliver_headers(self, mock_request):
        """Test that appropriate headers are sent"""
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.data = b"OK"
        mock_request.return_value = mock_response

        client = WebhookClient()
        payload = {"test": "data"}

        client.deliver("https://example.com/webhook", payload)

        call_args = mock_request.call_args
        # Headers passed to request() override default headers
        request_headers = call_args[1].get("headers", {})

        # Content-Type and User-Agent are set in PoolManager defaults
        # Content-Length is set per-request
        assert "Content-Length" in request_headers

        # Verify the request was made (headers are merged with defaults)
        assert mock_request.called

    def test_deliver_json_serialization(self):
        """Test that payload is properly JSON serialized"""
        with patch("urllib3.PoolManager.request") as mock_request:
            mock_response = MagicMock()
            mock_response.status = 200
            mock_request.return_value = mock_response

            client = WebhookClient()
            payload = {
                "event_type": "test",
                "timestamp": "2025-12-15T10:30:00Z",
                "data": {"key": "value"},
                "number": 42,
                "boolean": True,
                "none": None,
            }

            client.deliver("https://example.com/webhook", payload)

            # Check that body is JSON encoded
            body = mock_request.call_args[1]["body"]
            assert isinstance(body, bytes)

            # Verify it's valid JSON
            decoded = json.loads(body.decode("utf-8"))
            assert decoded == payload
