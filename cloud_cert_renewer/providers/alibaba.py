"""Alibaba Cloud adapter

Implements adapter for Alibaba Cloud CDN and Load Balancer certificate renewal.
"""

import os

from cloud_cert_renewer.auth.factory import CredentialProviderFactory
from cloud_cert_renewer.config import Credentials
from cloud_cert_renewer.providers.base import CloudAdapter


class AlibabaCloudAdapter(CloudAdapter):
    """Alibaba Cloud adapter (Alibaba Cloud Adapter)"""

    def _get_credential_client(
        self, credentials: Credentials, auth_method: str | None = None
    ) -> (
        "alibabacloud_credentials.client.Client"  # noqa: F821
    ):
        """
        Get credential client from credentials and auth_method
        :param credentials: Credentials object
        :param auth_method: Authentication method
            (if None, infer from credentials or env)
        :return: CredClient instance
        """
        if auth_method is None:
            # Try to get from environment variable
            auth_method = os.environ.get("AUTH_METHOD", "access_key").lower()

        # Create credential provider based on auth_method
        provider = CredentialProviderFactory.create(
            auth_method=auth_method, credentials=credentials
        )

        # Get credential client from provider
        return provider.get_credential_client()

    def update_cdn_certificate(
        self,
        domain_name: str,
        cert: str,
        cert_private_key: str,
        region: str,
        credentials: Credentials,
        auth_method: str | None = None,
    ) -> bool:
        """Update Alibaba Cloud CDN certificate (via Alibaba Cloud adapter)"""
        from cloud_cert_renewer.clients.alibaba import CdnCertRenewer

        credential_client = self._get_credential_client(credentials, auth_method)

        return CdnCertRenewer.renew_cert(
            domain_name=domain_name,
            cert=cert,
            cert_private_key=cert_private_key,
            region=region,
            credential_client=credential_client,
        )

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
        """Update Alibaba Cloud Load Balancer certificate (via Alibaba Cloud adapter)"""
        from cloud_cert_renewer.clients.alibaba import LoadBalancerCertRenewer

        credential_client = self._get_credential_client(credentials, auth_method)

        return LoadBalancerCertRenewer.renew_cert(
            instance_id=instance_id,
            listener_port=listener_port,
            cert=cert,
            cert_private_key=cert_private_key,
            region=region,
            credential_client=credential_client,
        )

    def get_current_cdn_certificate(
        self,
        domain_name: str,
        region: str,
        credentials: Credentials,
        auth_method: str | None = None,
    ) -> str | None:
        """Get Alibaba Cloud CDN current certificate (via Alibaba Cloud adapter)"""
        from cloud_cert_renewer.clients.alibaba import CdnCertRenewer

        credential_client = self._get_credential_client(credentials, auth_method)

        return CdnCertRenewer.get_current_cert(
            domain_name=domain_name,
            credential_client=credential_client,
        )

    def get_current_lb_certificate_fingerprint(
        self,
        instance_id: str,
        listener_port: int,
        region: str,
        credentials: Credentials,
        auth_method: str | None = None,
    ) -> str | None:
        """
        Get Alibaba Cloud Load Balancer current certificate fingerprint
        (via Alibaba Cloud adapter)
        """
        from cloud_cert_renewer.clients.alibaba import LoadBalancerCertRenewer

        credential_client = self._get_credential_client(credentials, auth_method)

        return LoadBalancerCertRenewer.get_current_cert_fingerprint(
            instance_id=instance_id,
            listener_port=listener_port,
            region=region,
            credential_client=credential_client,
        )
