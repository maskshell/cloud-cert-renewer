"""Webhook event data models

Defines data structures for webhook events.
"""

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal


@dataclass
class EventSource:
    """Event source information"""

    service_type: Literal["cdn", "lb"]
    cloud_provider: str
    region: str


@dataclass
class EventTarget:
    """Event target information"""

    domain_names: list[str] | None = None
    instance_ids: list[str] | None = None
    listener_port: int | None = None


@dataclass
class EventCertificate:
    """Certificate information"""

    fingerprint: str | None = None
    not_after: datetime | None = None
    not_before: datetime | None = None
    issuer: str | None = None


@dataclass
class EventResult:
    """Event result information"""

    status: Literal["success", "failure", "skipped", "started"]
    message: str
    error_code: str | None = None
    error_details: str | None = None
    retry_count: int = 0


@dataclass
class EventMetadata:
    """Event metadata"""

    version: str
    execution_time_ms: int | None = None
    total_resources: int | None = None
    successful_resources: int | None = None
    failed_resources: int | None = None
    force_update: bool = False
    dry_run: bool = False


@dataclass
class WebhookEvent:
    """Webhook event data"""

    event_type: Literal[
        "renewal_started",
        "renewal_success",
        "renewal_failed",
        "renewal_skipped",
        "batch_completed",
    ]
    source: EventSource
    target: EventTarget
    certificate: EventCertificate | None = None
    result: EventResult | None = None
    metadata: EventMetadata | None = None
    event_id: str = None
    timestamp: datetime = None

    def __post_init__(self) -> None:
        if self.event_id is None:
            self.event_id = str(uuid.uuid4())
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for JSON serialization"""
        data = asdict(self)

        # Convert datetime objects to ISO 8601 strings
        if self.timestamp:
            data["timestamp"] = self.timestamp.isoformat()

        if self.certificate:
            if self.certificate.not_after:
                data["certificate"][
                    "not_after"
                ] = self.certificate.not_after.isoformat()
            if self.certificate.not_before:
                data["certificate"][
                    "not_before"
                ] = self.certificate.not_before.isoformat()

        return data

    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps(self.to_dict(), default=str)
