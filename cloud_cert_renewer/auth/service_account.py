"""ServiceAccount credential provider

Provides credential retrieval based on Kubernetes ServiceAccount.
Uses RRSA (RAM Role for Service Account) for Alibaba Cloud authentication.
"""

import os

from alibabacloud_credentials.client import Client as CredClient
from alibabacloud_credentials.models import Config as CredConfig

from cloud_cert_renewer.auth.errors import AuthError
from cloud_cert_renewer.config import Credentials


class ServiceAccountCredentialProvider:
    """ServiceAccount credential provider (for Kubernetes environments with RRSA)"""

    def __init__(
        self,
        service_account_path: str = "/var/run/secrets/kubernetes.io/serviceaccount",
        role_arn: str | None = None,
        oidc_provider_arn: str | None = None,
        role_session_name: str | None = None,
    ) -> None:
        """
        Initialize ServiceAccount credential provider
        :param service_account_path: ServiceAccount token path (default:
            /var/run/secrets/kubernetes.io/serviceaccount)
        :param role_arn: Alibaba Cloud RAM Role ARN (if None, read from env)
        :param oidc_provider_arn: OIDC Provider ARN (if None, read from env)
        :param role_session_name: Session name (default:
            "cert-renewer-service-account-session")
        """
        self.service_account_path = service_account_path
        self.role_arn = role_arn
        self.oidc_provider_arn = oidc_provider_arn
        self.role_session_name = role_session_name or (
            "cert-renewer-service-account-session"
        )

    def _get_role_arn(self) -> str:
        """Get role ARN from parameter or environment variable"""
        if self.role_arn:
            return self.role_arn
        role_arn = os.environ.get("ALIBABA_CLOUD_ROLE_ARN") or os.environ.get(
            "CLOUD_ROLE_ARN"
        )
        if not role_arn:
            raise AuthError(
                "ServiceAccount authentication requires role_arn. "
                "Set ALIBABA_CLOUD_ROLE_ARN or CLOUD_ROLE_ARN environment variable, "
                "or pass role_arn parameter. "
                "Note: RRSA must be enabled and configured on your Kubernetes cluster."
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
            raise AuthError(
                "ServiceAccount authentication requires oidc_provider_arn. "
                "Set ALIBABA_CLOUD_OIDC_PROVIDER_ARN or CLOUD_OIDC_PROVIDER_ARN "
                "environment variable, or pass oidc_provider_arn parameter."
            )
        return oidc_provider_arn

    def _get_oidc_token_file_path(self) -> str:
        """Get OIDC token file path from ServiceAccount token"""
        return os.path.join(self.service_account_path, "token")

    def get_credential_client(self) -> CredClient:
        """
        Get Alibaba Cloud Credentials client for ServiceAccount authentication
        Reads Kubernetes ServiceAccount token and uses RRSA/OIDC auth
        :return: CredClient instance
        """
        oidc_token_file = self._get_oidc_token_file_path()

        # Verify token file exists
        if not os.path.exists(oidc_token_file):
            raise AuthError(
                f"ServiceAccount token file not found: {oidc_token_file}. "
                f"Ensure the pod is running with a ServiceAccount and "
                f"RRSA is properly configured."
            )

        config = CredConfig(
            type="oidc_role_arn",
            role_arn=self._get_role_arn(),
            oidc_provider_arn=self._get_oidc_provider_arn(),
            oidc_token_file_path=oidc_token_file,
            role_session_name=self.role_session_name,
        )
        return CredClient(config)

    def get_credentials(self) -> Credentials:
        """
        Get ServiceAccount credentials (temporary credentials from AssumeRoleWithOIDC)
        Reads the Kubernetes ServiceAccount token and exchanges it for
        temporary Alibaba Cloud credentials using RRSA/OIDC
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
