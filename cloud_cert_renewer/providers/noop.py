"""No-op cloud adapter.

This adapter is intended for smoke tests and local validation. It exercises the
high-level renewal flow without performing any network calls.
"""

from __future__ import annotations

import logging

from cloud_cert_renewer.auth.factory import CredentialProviderFactory
from cloud_cert_renewer.config import Credentials
from cloud_cert_renewer.providers.base import CloudAdapter

logger = logging.getLogger(__name__)


class NoopAdapter(CloudAdapter):
    """A no-op adapter that always reports success and never calls cloud APIs."""

    def _touch_auth(self, credentials: Credentials, auth_method: str | None) -> None:
        method = (auth_method or "access_key").lower()
        provider = CredentialProviderFactory.create(
            auth_method=method,
            credentials=credentials,
        )
        provider.get_credential_client()

    def update_cdn_certificate(
        self,
        domain_name: str,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
        auth_method: str | None = None,
    ) -> bool:
        self._touch_auth(credentials, auth_method)
        logger.info(
            "NOOP adapter: would update CDN certificate: domain=%s, region=%s",
            domain_name,
            region,
        )
        return True

    def update_load_balancer_certificate(
        self,
        instance_id: str,
        listener_port: int,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
        auth_method: str | None = None,
    ) -> bool:
        self._touch_auth(credentials, auth_method)
        logger.info(
            "NOOP adapter: would update Load Balancer certificate: "
            "instance_id=%s, port=%s, region=%s",
            instance_id,
            listener_port,
            region,
        )
        return True

    def get_current_cdn_certificate(
        self,
        domain_name: str,
        region: str,
        credentials: Credentials,
        auth_method: str | None = None,
    ) -> str | None:
        self._touch_auth(credentials, auth_method)
        return None

    def get_current_lb_certificate_fingerprint(
        self,
        instance_id: str,
        listener_port: int,
        region: str,
        credentials: Credentials,
        auth_method: str | None = None,
    ) -> str | None:
        self._touch_auth(credentials, auth_method)
        return None
