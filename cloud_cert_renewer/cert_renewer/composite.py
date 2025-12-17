"""Composite certificate renewer

Implements composite pattern for handling multiple resources.
"""

import logging
import time

from cloud_cert_renewer import __version__
from cloud_cert_renewer.cert_renewer.base import BaseCertRenewer
from cloud_cert_renewer.webhook.events import (
    EventMetadata,
    EventResult,
    EventSource,
    EventTarget,
    WebhookEvent,
)

logger = logging.getLogger(__name__)


class CompositeCertRenewer:
    """Composite certificate renewer"""

    def __init__(self, renewers: list[BaseCertRenewer]) -> None:
        """
        Initialize composite renewer
        :param renewers: List of certificate renewers
        """
        self.renewers = renewers

    def renew(self) -> bool:
        """
        Renew all certificates
        Executes renewal for all managed resources using "best effort" strategy.
        If any renewal fails, logs the error and continues with others.
        :return: True if ALL renewals succeeded, False if ANY failed
        """
        if not self.renewers:
            logger.warning("No resources to renew")
            return True

        failures = 0
        total = len(self.renewers)

        logger.info("Starting batch renewal for %d resources...", total)

        for i, renewer in enumerate(self.renewers, 1):
            try:
                # We can't easily get the target name here without modifying base class,
                # but the renewer itself logs detailed info.
                logger.info("[%d/%d] Processing resource...", i, total)
                if not renewer.renew():
                    failures += 1
            except Exception as e:
                logger.exception(
                    "[%d/%d] Unexpected error during renewal: %s", i, total, e
                )
                failures += 1

        # Send batch summary webhook if webhook service is available
        # Add a small delay to ensure all individual webhook threads have been started
        # Webhook failures are non-critical and should not affect the main process
        if self.renewers and self.renewers[0]._webhook_service:
            try:
                time.sleep(0.05)  # Small delay to ensure individual webhooks are queued
                self._send_batch_summary_webhook(total, failures)
            except Exception as e:
                # Log but don't raise - webhook failures are non-critical
                logger.warning(
                    "Failed to send batch summary webhook (non-critical): %s", e
                )

        if failures > 0:
            logger.error(
                "Batch renewal completed with errors: %d/%d failed", failures, total
            )
            return False

        logger.info(
            "Batch renewal completed successfully: %d/%d succeeded", total, total
        )
        return True

    def _send_batch_summary_webhook(self, total: int, failures: int) -> None:
        """Send batch completion webhook"""
        if not self.renewers:
            return

        # Get reference to first renewer for config
        first_renewer = self.renewers[0]
        webhook_service = first_renewer._webhook_service

        if not webhook_service or not webhook_service.is_enabled("batch_completed"):
            return

        # Prepare event source
        source = EventSource(
            service_type=first_renewer.config.service_type,
            cloud_provider=first_renewer.config.cloud_provider,
            region=first_renewer._get_region(),
        )

        # Prepare event target (summary of all resources)
        target = EventTarget()
        if first_renewer.config.service_type == "cdn":
            all_domains = []
            for renewer in self.renewers:
                if renewer.config.cdn_config:
                    all_domains.extend(renewer.config.cdn_config.domain_names)
            target.domain_names = list(set(all_domains))  # Remove duplicates
        else:  # lb
            all_instances = []
            for renewer in self.renewers:
                if renewer.config.lb_config:
                    all_instances.extend(renewer.config.lb_config.instance_ids)
            target.instance_ids = list(set(all_instances))  # Remove duplicates
            if first_renewer.config.lb_config:
                target.listener_port = first_renewer.config.lb_config.listener_port

        # Prepare result
        result = EventResult(
            status="success" if failures == 0 else "failure",
            message=f"Batch renewal completed: {total - failures}/{total} succeeded",
        )

        # Prepare metadata
        metadata = EventMetadata(
            version=__version__,
            total_resources=total,
            successful_resources=total - failures,
            failed_resources=failures,
            force_update=first_renewer.config.force_update,
            dry_run=first_renewer.config.dry_run,
        )

        # Create and send event
        event = WebhookEvent(
            event_type="batch_completed",
            source=source,
            target=target,
            result=result,
            metadata=metadata,
        )

        # Send asynchronously (send_event already handles threading)
        # Webhook failures are non-critical and handled internally
        try:
            webhook_service.send_event(event)
        except Exception as e:
            # Log but don't raise - webhook failures are non-critical
            logger.warning(
                "Failed to send batch summary webhook event (non-critical): %s", e
            )
