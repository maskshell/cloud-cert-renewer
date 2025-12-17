#!/usr/bin/env python3
"""Test webhook delivery with actual webhook URL from .env file

This script creates a test webhook event and sends it to the configured
webhook URL. It helps verify that webhook delivery works correctly and detects
errors in response body.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

# Configure logging to show webhook client details
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger("cloud_cert_renewer.webhook.client")
logger.setLevel(logging.DEBUG)

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ruff: noqa: E402
from cloud_cert_renewer import __version__
from cloud_cert_renewer.webhook.client import WebhookClient
from cloud_cert_renewer.webhook.events import (
    EventCertificate,
    EventMetadata,
    EventResult,
    EventSource,
    EventTarget,
    WebhookEvent,
)
from cloud_cert_renewer.webhook.formatters import MessageFormatterFactory


def main():
    """Main test function"""
    # Load .env file
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"✓ Loaded .env file from: {env_path}")
    else:
        load_dotenv()  # Try to load from current directory
        print("⚠ .env file not found, using environment variables")

    # Get webhook URL from environment
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        print("❌ Error: WEBHOOK_URL environment variable is not set")
        print("\nPlease set WEBHOOK_URL in your .env file or environment:")
        print("  WEBHOOK_URL=https://your-webhook-url-here")
        sys.exit(1)

    print(
        f"✓ Webhook URL: {webhook_url[:50]}..."
        if len(webhook_url) > 50
        else f"✓ Webhook URL: {webhook_url}"
    )
    print()

    # Get message format (default: wechat_work if URL contains weixin.qq.com,
    # otherwise generic)
    message_format = os.getenv("WEBHOOK_MESSAGE_FORMAT", "generic")
    if "weixin.qq.com" in webhook_url or "work.weixin.qq.com" in webhook_url:
        message_format = "wechat_work"
        print(f"✓ Detected WeChat Work webhook, using format: {message_format}")

    # Create a test webhook event
    print("\n📋 Creating test webhook event...")
    source = EventSource(
        service_type="cdn",
        cloud_provider="alibaba",
        region="cn-hangzhou",
    )
    target = EventTarget(domain_names=["example.com", "test.example.com"])
    certificate = EventCertificate(
        fingerprint="sha256:test1234567890abcdef",
        not_after=datetime.now(timezone.utc).replace(year=2026),
        issuer="Test CA",
    )
    result = EventResult(
        status="success",
        message="Test certificate renewal completed successfully",
    )
    metadata = EventMetadata(
        version=__version__,
        execution_time_ms=1234,
        dry_run=True,
    )

    event = WebhookEvent(
        event_type="renewal_success",
        source=source,
        target=target,
        certificate=certificate,
        result=result,
        metadata=metadata,
    )

    print(f"✓ Event created: {event.event_type}")
    print(f"  Event ID: {event.event_id}")
    print(f"  Timestamp: {event.timestamp}")

    # Format the event
    print("\n🔧 Formatting webhook payload...")
    formatter = MessageFormatterFactory.create(message_format)
    payload = formatter.format(event)

    print(f"✓ Payload formatted using {message_format} formatter")
    print("\n📤 Payload to send:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    print()

    # Create webhook client for synchronous delivery
    print("🚀 Sending webhook synchronously...")
    print("   (This will show detailed response information)")
    print()

    webhook_client = WebhookClient(
        timeout=int(os.getenv("WEBHOOK_TIMEOUT", "30")),
        retry_attempts=int(os.getenv("WEBHOOK_RETRY_ATTEMPTS", "3")),
        retry_delay=float(os.getenv("WEBHOOK_RETRY_DELAY", "1.0")),
    )

    try:
        # Send webhook synchronously to get immediate result
        success = webhook_client.deliver(webhook_url, payload)

        print()
        if success:
            print("✅ Webhook sent successfully!")
            print("\n💡 Note: Even if HTTP status is 200, the client checks the")
            print(
                "   response body for error codes (e.g., WeChat Work's errcode field)"
            )
            print("\n   If you didn't receive the message in WeChat Work, check:")
            print("   1. Webhook URL is correct and active")
            print("   2. Message format matches WeChat Work requirements")
            print("   3. Check WeChat Work webhook logs/console")
            print("   4. Verify the webhook robot is enabled in WeChat Work")
            print("\n   The response body was checked for errcode field.")
            print("   If errcode != 0, the delivery would have been marked as failed.")
        else:
            print("❌ Webhook delivery failed!")
            print("\n💡 Common issues:")
            print("   - Invalid webhook URL")
            print("   - Network connectivity issues")
            print("   - Webhook service returned error in response body")
            print("     (e.g., WeChat Work errcode != 0)")
            print("   - Payload format not accepted by webhook service")
            print("\n   Check the DEBUG logs above for detailed error information.")
            print("   Look for lines starting with 'WARNING:' or 'ERROR:'")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error sending webhook: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    print("\n✨ Test completed successfully!")


if __name__ == "__main__":
    main()
