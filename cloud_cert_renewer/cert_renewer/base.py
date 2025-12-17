"""Certificate renewer base class

Defines abstract interfaces and template methods for certificate renewers.
"""

import logging
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime

from cloud_cert_renewer import __version__
from cloud_cert_renewer.config import AppConfig
from cloud_cert_renewer.webhook.events import (
    EventCertificate,
    EventMetadata,
    EventResult,
    EventSource,
    EventTarget,
    WebhookEvent,
)

logger = logging.getLogger(__name__)


class CertValidationError(Exception):
    """Certificate validation error exception"""

    pass


class BaseCertRenewer(ABC):
    """Certificate renewer base class (Template Method pattern)"""

    def __init__(self, config: AppConfig) -> None:
        """
        Initialize certificate renewer
        :param config: Application configuration
        """
        self.config = config
        self._webhook_service = None
        self._renewal_start_time = None

        # Initialize webhook service if configured
        if config.webhook_config and config.webhook_config.url:
            from cloud_cert_renewer.webhook import WebhookService

            self._webhook_service = WebhookService(
                url=config.webhook_config.url,
                timeout=config.webhook_config.timeout,
                retry_attempts=config.webhook_config.retry_attempts,
                retry_delay=config.webhook_config.retry_delay,
                enabled_events=config.webhook_config.enabled_events,
                message_format=config.webhook_config.message_format,
            )
            logger.info(
                "Webhook service initialized: url=%s, enabled_events=%s",
                config.webhook_config.url[:50] + "..."
                if len(config.webhook_config.url) > 50
                else config.webhook_config.url,
                config.webhook_config.enabled_events,
            )
        else:
            logger.debug(
                "Webhook service not initialized: webhook_config=%s, url=%s",
                config.webhook_config is not None,
                config.webhook_config.url if config.webhook_config else None,
            )

    def _send_webhook_event(
        self,
        event_type: str,
        cert_info: tuple[str, str, str] | None = None,
        result: EventResult | None = None,
    ) -> None:
        """
        Send webhook event if configured.
        Webhook failures are non-critical and should not affect the main renewal
        process.

        :param event_type: Type of event
        :param cert_info: Certificate info tuple
            (cert, cert_private_key, domain_or_instance)
        :param result: Event result information
        """
        if not self._webhook_service or not self._webhook_service.is_enabled(
            event_type
        ):
            return

        try:
            # Prepare event source
            source = EventSource(
                service_type=self.config.service_type,
                cloud_provider=self.config.cloud_provider,
                region=self._get_region(),
            )

            # Prepare event target
            target = EventTarget()
            if cert_info:
                _, _, domain_or_instance = cert_info
                if self.config.service_type == "cdn":
                    target.domain_names = [domain_or_instance]
                else:  # lb
                    target.instance_ids = [domain_or_instance]
                    if self.config.lb_config:
                        target.listener_port = self.config.lb_config.listener_port

            # Prepare certificate info if available
            certificate = None
            if cert_info and event_type in [
                "renewal_started",
                "renewal_success",
                "renewal_skipped",
            ]:
                cert, _, _ = cert_info
                fingerprint = self._calculate_fingerprint(cert)
                cert_data = self._parse_cert_info(cert)
                certificate = EventCertificate(
                    fingerprint=fingerprint,
                    not_after=cert_data.get("not_after"),
                    not_before=cert_data.get("not_before"),
                    issuer=cert_data.get("issuer"),
                )

            # Prepare metadata
            execution_time_ms = None
            if self._renewal_start_time:
                execution_time_ms = int((time.time() - self._renewal_start_time) * 1000)

            metadata = EventMetadata(
                version=__version__,
                execution_time_ms=execution_time_ms,
                force_update=self.config.force_update,
                dry_run=self.config.dry_run,
            )

            # Create and send event
            event = WebhookEvent(
                event_type=event_type,
                source=source,
                target=target,
                certificate=certificate,
                result=result,
                metadata=metadata,
            )

            # Send asynchronously without blocking
            # Webhook failures are non-critical and should not affect the main process
            def send_webhook_safely():
                try:
                    self._webhook_service.send_event(event)
                except Exception as e:
                    # Log but don't raise - webhook failures are non-critical
                    logger.warning(
                        "Failed to send webhook event (non-critical): "
                        "event_type=%s, error=%s",
                        event_type,
                        e,
                    )

            threading.Thread(
                target=send_webhook_safely,
                daemon=True,
            ).start()
        except Exception as e:
            # Log but don't raise - webhook failures are non-critical
            # This ensures webhook failures don't cause Pod restarts
            logger.warning(
                "Failed to prepare webhook event (non-critical): "
                "event_type=%s, error=%s",
                event_type,
                e,
            )

    def _get_region(self) -> str:
        """Get region from configuration"""
        if self.config.service_type == "cdn" and self.config.cdn_config:
            return self.config.cdn_config.region
        elif self.config.service_type == "lb" and self.config.lb_config:
            return self.config.lb_config.region
        return "cn-hangzhou"  # Default region

    def _parse_cert_info(self, cert: str) -> dict[str, datetime | str | None]:
        """
        Parse certificate information for webhook payload
        :param cert: Certificate content (PEM format)
        :return: Dictionary with certificate info
        """
        try:
            from cryptography import x509
            from cryptography.hazmat.backends import default_backend

            # Load certificate from PEM format
            cert_obj = x509.load_pem_x509_certificate(
                cert.encode("utf-8"), default_backend()
            )

            return {
                "not_after": cert_obj.not_valid_after_utc,
                "not_before": cert_obj.not_valid_before_utc,
                "issuer": cert_obj.issuer.rfc4514_string(),
            }
        except Exception as e:
            logger.debug("Failed to parse certificate info for webhook: %s", e)
            return {
                "not_after": None,
                "not_before": None,
                "issuer": None,
            }

    def renew(self) -> bool:
        """
        Renew certificate (template method)
        Defines the standard certificate renewal process:
        1. Validate certificate
        2. Compare certificate fingerprints (if force update is not required)
        3. Execute renewal
        :return: Whether successful
        """
        # Get certificate and private key
        cert, cert_private_key, domain_or_instance = self._get_cert_info()
        cert_info = (cert, cert_private_key, domain_or_instance)

        # Track start time for metrics
        self._renewal_start_time = time.time()

        logger.info(
            "Renewal started: service_type=%s, cloud_provider=%s, "
            "target=%s, force_update=%s",
            self.config.service_type,
            self.config.cloud_provider,
            domain_or_instance,
            self.config.force_update,
        )

        # Send renewal started webhook
        self._send_webhook_event("renewal_started", cert_info=cert_info)

        # Step 1: Validate certificate
        if not self._validate_cert(cert, domain_or_instance):
            raise CertValidationError(
                f"Certificate validation failed: domain {domain_or_instance} "
                f"is not in the certificate or certificate has expired"
            )

        # Step 2: Compare certificate fingerprints (if force update is not required)
        if not self.config.force_update:
            current_fingerprint = self.get_current_cert_fingerprint()
            if current_fingerprint:
                new_fingerprint = self._calculate_fingerprint(cert)
                if new_fingerprint == current_fingerprint:
                    logger.info(
                        "Certificate unchanged, skipping renewal: %s, fingerprint=%s",
                        domain_or_instance,
                        new_fingerprint[:20] + "...",
                    )
                    # Send renewal skipped webhook
                    self._send_webhook_event(
                        "renewal_skipped",
                        cert_info=cert_info,
                        result=EventResult(
                            status="skipped",
                            message="Certificate unchanged, skipping renewal",
                        ),
                    )
                    return True
            else:
                logger.info(
                    "Current certificate fingerprint unavailable, "
                    "will proceed with renewal: %s",
                    domain_or_instance,
                )
        else:
            logger.info(
                "Force update mode enabled, will update even if certificate "
                "is the same: %s",
                domain_or_instance,
            )

        # Step 3: Execute renewal
        if self.config.dry_run:
            logger.info(
                "DRY-RUN: Would update certificate for %s (skipping API call)",
                domain_or_instance,
            )
            logger.info("DRY-RUN: Certificate renewal simulation completed")
            # Send dry-run success webhook
            self._send_webhook_event(
                "renewal_success",
                cert_info=cert_info,
                result=EventResult(
                    status="success",
                    message="DRY-RUN: Certificate renewal simulation completed",
                ),
            )
            return True

        success = self._do_renew(cert, cert_private_key)
        if success:
            logger.info("Renewal succeeded: %s", domain_or_instance)
            # Send renewal success webhook
            self._send_webhook_event(
                "renewal_success",
                cert_info=cert_info,
                result=EventResult(
                    status="success",
                    message="Certificate renewed successfully",
                ),
            )
        else:
            logger.error("Renewal failed: %s", domain_or_instance)
            # Send renewal failed webhook
            self._send_webhook_event(
                "renewal_failed",
                cert_info=cert_info,
                result=EventResult(
                    status="failure",
                    message="Certificate renewal failed",
                    error_code="RENEWAL_FAILED",
                ),
            )
        return success

    @abstractmethod
    def _get_cert_info(self) -> tuple[str, str, str]:
        """
        Get certificate information
        :return: (cert, cert_private_key, domain_or_instance)
        """
        pass

    @abstractmethod
    def _validate_cert(self, cert: str, domain_or_instance: str) -> bool:
        """
        Validate certificate
        :param cert: Certificate content
        :param domain_or_instance: Domain name or instance ID
        :return: Whether valid
        """
        pass

    @abstractmethod
    def _calculate_fingerprint(self, cert: str) -> str:
        """
        Calculate certificate fingerprint
        :param cert: Certificate content
        :return: Certificate fingerprint
        """
        pass

    @abstractmethod
    def get_current_cert_fingerprint(self) -> str | None:
        """
        Get current certificate fingerprint
        :return: Certificate fingerprint, or None if query fails
        """
        pass

    @abstractmethod
    def _do_renew(self, cert: str, cert_private_key: str) -> bool:
        """
        Execute certificate renewal (subclasses implement specific logic)
        :param cert: Certificate content
        :param cert_private_key: Certificate private key
        :return: Whether successful
        """
        pass
