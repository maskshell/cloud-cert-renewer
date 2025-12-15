"""Tests for webhook event models"""

import json
from datetime import datetime, timezone

from cloud_cert_renewer.webhook.events import (
    EventCertificate,
    EventMetadata,
    EventResult,
    EventSource,
    EventTarget,
    WebhookEvent,
)


class TestEventSource:
    """Test EventSource model"""

    def test_event_source_creation(self):
        """Test EventSource creation"""
        source = EventSource(
            service_type="cdn", cloud_provider="alibaba", region="cn-hangzhou"
        )
        assert source.service_type == "cdn"
        assert source.cloud_provider == "alibaba"
        assert source.region == "cn-hangzhou"


class TestEventTarget:
    """Test EventTarget model"""

    def test_event_target_cdn(self):
        """Test EventTarget for CDN"""
        target = EventTarget(domain_names=["example.com", "www.example.com"])
        assert target.domain_names == ["example.com", "www.example.com"]
        assert target.instance_ids is None
        assert target.listener_port is None

    def test_event_target_lb(self):
        """Test EventTarget for Load Balancer"""
        target = EventTarget(instance_ids=["lb-12345"], listener_port=443)
        assert target.instance_ids == ["lb-12345"]
        assert target.listener_port == 443
        assert target.domain_names is None


class TestEventCertificate:
    """Test EventCertificate model"""

    def test_event_certificate(self):
        """Test EventCertificate creation"""
        cert = EventCertificate(
            fingerprint="sha256:abcd1234",
            not_after=datetime(2026, 1, 1, tzinfo=timezone.utc),
            not_before=datetime(2025, 1, 1, tzinfo=timezone.utc),
            issuer="Let's Encrypt",
        )
        assert cert.fingerprint == "sha256:abcd1234"
        assert cert.not_after.year == 2026
        assert cert.not_before.year == 2025
        assert cert.issuer == "Let's Encrypt"


class TestEventResult:
    """Test EventResult model"""

    def test_event_result_success(self):
        """Test successful EventResult"""
        result = EventResult(
            status="success", message="Certificate renewed successfully"
        )
        assert result.status == "success"
        assert result.message == "Certificate renewed successfully"
        assert result.error_code is None
        assert result.error_details is None

    def test_event_result_failure(self):
        """Test failure EventResult"""
        result = EventResult(
            status="failure",
            message="Certificate renewal failed",
            error_code="API_ERROR",
            error_details="Cloud provider API returned error",
        )
        assert result.status == "failure"
        assert result.error_code == "API_ERROR"
        assert result.error_details == "Cloud provider API returned error"


class TestEventMetadata:
    """Test EventMetadata model"""

    def test_event_metadata(self):
        """Test EventMetadata creation"""
        metadata = EventMetadata(
            version="0.2.1-rc1",
            execution_time_ms=1500,
            total_resources=3,
            successful_resources=3,
            failed_resources=0,
            force_update=False,
            dry_run=False,
        )
        assert metadata.version == "0.2.1-rc1"
        assert metadata.execution_time_ms == 1500
        assert metadata.total_resources == 3
        assert metadata.successful_resources == 3
        assert metadata.failed_resources == 0
        assert metadata.force_update is False
        assert metadata.dry_run is False


class TestWebhookEvent:
    """Test WebhookEvent model"""

    def test_webhook_event_creation(self):
        """Test WebhookEvent creation"""
        source = EventSource(
            service_type="cdn", cloud_provider="alibaba", region="cn-hangzhou"
        )
        target = EventTarget(domain_names=["example.com"])
        cert = EventCertificate(fingerprint="sha256:abcd1234")
        result = EventResult(status="success", message="Renewed")
        metadata = EventMetadata(version="0.2.1-rc1")

        event = WebhookEvent(
            event_type="renewal_success",
            source=source,
            target=target,
            certificate=cert,
            result=result,
            metadata=metadata,
        )

        assert event.event_type == "renewal_success"
        assert event.source == source
        assert event.target == target
        assert event.certificate == cert
        assert event.result == result
        assert event.metadata == metadata
        assert event.event_id is not None  # Auto-generated
        assert event.timestamp is not None  # Auto-generated

    def test_webhook_event_to_dict(self):
        """Test WebhookEvent to_dict conversion"""
        event = WebhookEvent(
            event_type="renewal_started",
            source=EventSource(
                service_type="cdn", cloud_provider="alibaba", region="cn-hangzhou"
            ),
            target=EventTarget(domain_names=["example.com"]),
            certificate=EventCertificate(
                fingerprint="sha256:abcd1234",
                not_after=datetime(2026, 1, 1, tzinfo=timezone.utc),
            ),
            metadata=EventMetadata(version="0.2.1-rc1"),
        )

        data = event.to_dict()

        assert data["event_type"] == "renewal_started"
        assert data["event_id"] == event.event_id
        assert "timestamp" in data
        assert data["source"]["service_type"] == "cdn"
        assert data["target"]["domain_names"] == ["example.com"]
        assert data["certificate"]["fingerprint"] == "sha256:abcd1234"
        assert data["certificate"]["not_after"] == "2026-01-01T00:00:00+00:00"

    def test_webhook_event_to_json(self):
        """Test WebhookEvent to_json conversion"""
        event = WebhookEvent(
            event_type="renewal_failed",
            source=EventSource(
                service_type="lb", cloud_provider="aws", region="us-east-1"
            ),
            target=EventTarget(instance_ids=["lb-12345"], listener_port=443),
            result=EventResult(
                status="failure", message="Failed", error_code="API_ERROR"
            ),
        )

        json_str = event.to_json()
        data = json.loads(json_str)

        assert data["event_type"] == "renewal_failed"
        assert data["source"]["cloud_provider"] == "aws"
        assert data["target"]["instance_ids"] == ["lb-12345"]
        assert data["result"]["status"] == "failure"
        assert data["result"]["error_code"] == "API_ERROR"

    def test_webhook_event_post_init(self):
        """Test WebhookEvent __post_init__ method"""
        event = WebhookEvent(
            event_type="renewal_skipped",
            source=EventSource(
                service_type="cdn", cloud_provider="alibaba", region="cn-hangzhou"
            ),
            target=EventTarget(domain_names=["example.com"]),
            result=EventResult(status="skipped", message="Skipped"),
        )

        # Check that event_id and timestamp are set
        assert event.event_id is not None
        assert len(event.event_id) == 36  # UUID v4 length
        assert event.timestamp is not None
        assert isinstance(event.timestamp, datetime)
        assert event.timestamp.tzinfo == timezone.utc

    def test_webhook_event_none_values(self):
        """Test WebhookEvent with optional None values"""
        event = WebhookEvent(
            event_type="batch_completed",
            source=EventSource(
                service_type="cdn", cloud_provider="alibaba", region="cn-hangzhou"
            ),
            target=EventTarget(),
            result=EventResult(status="success", message="Batch completed"),
            metadata=EventMetadata(
                version="0.2.1-rc1",
                total_resources=5,
                successful_resources=5,
                failed_resources=0,
            ),
        )

        data = event.to_dict()

        # Optional fields should be None or omitted
        assert data["certificate"] is None
        assert data["target"]["domain_names"] is None
        assert data["target"]["instance_ids"] is None
        assert data["target"]["listener_port"] is None
        assert data["metadata"]["total_resources"] == 5
