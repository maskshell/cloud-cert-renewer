"""IAM Role credential provider

Provides credential retrieval based on IAM Role (for IAM roles in cloud environments).
"""

import os

from alibabacloud_credentials.client import Client as CredClient
from alibabacloud_credentials.models import Config as CredConfig

from cloud_cert_renewer.auth.errors import AuthError
from cloud_cert_renewer.config import Credentials


class IAMRoleCredentialProvider:
    """IAM Role credential provider (for IAM roles in cloud environments)"""

    def __init__(
        self,
        role_arn: str,
        role_session_name: str | None = None,
        access_key_id: str | None = None,
        access_key_secret: str | None = None,
    ) -> None:
        """
        Initialize IAM Role credential provider
        :param role_arn: IAM Role ARN
        :param role_session_name: Session name (optional)
        :param access_key_id: AccessKey ID for assuming role
            (if None, read from env)
        :param access_key_secret: AccessKey Secret for assuming role
            (if None, read from env)
        """
        self.role_arn = role_arn
        self.role_session_name = role_session_name or "cert-renewer-session"
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret

    def _get_access_key_id(self) -> str:
        """Get access_key_id from parameter or environment variable"""
        if self.access_key_id:
            return self.access_key_id
        access_key_id = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID") or os.environ.get(
            "CLOUD_ACCESS_KEY_ID"
        )
        if not access_key_id:
            raise AuthError(
                "IAM Role authentication requires access_key_id. "
                "Set ALIBABA_CLOUD_ACCESS_KEY_ID or "
                "CLOUD_ACCESS_KEY_ID environment variable, "
                "or pass access_key_id parameter."
            )
        return access_key_id

    def _get_access_key_secret(self) -> str:
        """Get access_key_secret from parameter or environment variable"""
        if self.access_key_secret:
            return self.access_key_secret
        access_key_secret = os.environ.get(
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET"
        ) or os.environ.get("CLOUD_ACCESS_KEY_SECRET")
        if not access_key_secret:
            raise AuthError(
                "IAM Role authentication requires access_key_secret. "
                "Set ALIBABA_CLOUD_ACCESS_KEY_SECRET or CLOUD_ACCESS_KEY_SECRET "
                "environment variable, or pass access_key_secret parameter."
            )
        return access_key_secret

    def get_credential_client(self) -> CredClient:
        """
        Get Alibaba Cloud Credentials client for RAM Role ARN authentication
        :return: CredClient instance
        """
        config = CredConfig(
            type="ram_role_arn",
            access_key_id=self._get_access_key_id(),
            access_key_secret=self._get_access_key_secret(),
            role_arn=self.role_arn,
            role_session_name=self.role_session_name,
        )
        return CredClient(config)

    def get_credentials(self) -> Credentials:
        """
        Get IAM Role credentials (temporary credentials from AssumeRole)
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
