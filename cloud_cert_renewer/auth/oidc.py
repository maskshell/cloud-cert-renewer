"""OIDC credential provider

Provides credential retrieval based on OIDC (OpenID Connect) for RRSA
(RAM Role for Service Account) in Kubernetes environments.
"""

import os

from alibabacloud_credentials.client import Client as CredClient
from alibabacloud_credentials.models import Config as CredConfig

from cloud_cert_renewer.config import Credentials


class OidcCredentialProvider:
    """OIDC credential provider (for RRSA in Kubernetes environments)"""

    def __init__(
        self,
        role_arn: str | None = None,
        oidc_provider_arn: str | None = None,
        oidc_token_file_path: str | None = None,
        role_session_name: str | None = None,
    ) -> None:
        """
        Initialize OIDC credential provider
        :param role_arn: Alibaba Cloud RAM Role ARN (if None, read from env)
        :param oidc_provider_arn: OIDC Provider ARN (if None, read from env)
        :param oidc_token_file_path: Path to OIDC token file (if None, read from env)
        :param role_session_name: Session name (default: "cert-renewer-oidc-session")
        """
        self.role_arn = role_arn
        self.oidc_provider_arn = oidc_provider_arn
        self.oidc_token_file_path = oidc_token_file_path
        self.role_session_name = role_session_name or "cert-renewer-oidc-session"

    def _get_role_arn(self) -> str:
        """Get role ARN from parameter or environment variable"""
        if self.role_arn:
            return self.role_arn
        role_arn = os.environ.get("ALIBABA_CLOUD_ROLE_ARN") or os.environ.get(
            "CLOUD_ROLE_ARN"
        )
        if not role_arn:
            raise ValueError(
                "OIDC authentication requires role_arn. "
                "Set ALIBABA_CLOUD_ROLE_ARN or CLOUD_ROLE_ARN environment variable, "
                "or pass role_arn parameter."
            )
        return role_arn

    def _get_oidc_provider_arn(self) -> str:
        """Get OIDC provider ARN from parameter or environment variable"""
        if self.oidc_provider_arn:
            return self.oidc_provider_arn
        oidc_provider_arn = os.environ.get(
            "ALIBABA_CLOUD_OIDC_PROVIDER_ARN"
        ) or os.environ.get("CLOUD_OIDC_PROVIDER_ARN")
        if not oidc_provider_arn:
            raise ValueError(
                "OIDC authentication requires oidc_provider_arn. "
                "Set ALIBABA_CLOUD_OIDC_PROVIDER_ARN or CLOUD_OIDC_PROVIDER_ARN "
                "environment variable, or pass oidc_provider_arn parameter."
            )
        return oidc_provider_arn

    def _get_oidc_token_file_path(self) -> str | None:
        """Get OIDC token file path from parameter or environment variable"""
        if self.oidc_token_file_path:
            return self.oidc_token_file_path
        return os.environ.get("ALIBABA_CLOUD_OIDC_TOKEN_FILE") or os.environ.get(
            "CLOUD_OIDC_TOKEN_FILE"
        )

    def get_credential_client(self) -> CredClient:
        """
        Get Alibaba Cloud Credentials client for OIDC authentication
        :return: CredClient instance
        """
        config = CredConfig(
            type="oidc_role_arn",
            role_arn=self._get_role_arn(),
            oidc_provider_arn=self._get_oidc_provider_arn(),
            oidc_token_file_path=self._get_oidc_token_file_path(),
            role_session_name=self.role_session_name,
        )
        return CredClient(config)

    def get_credentials(self) -> Credentials:
        """
        Get OIDC credentials (temporary credentials from AssumeRoleWithOIDC)
        :return: Credentials object with temporary access_key_id, access_key_secret,
            and security_token
        """
        cred_client = self.get_credential_client()
        credential = cred_client.get_credential()

        return Credentials(
            access_key_id=credential.access_key_id,
            access_key_secret=credential.access_key_secret,
            security_token=credential.security_token,
        )
