"""AccessKey credential provider

Provides credential retrieval based on AccessKey ID and Secret.
"""

from alibabacloud_credentials.client import Client as CredClient
from alibabacloud_credentials.models import Config as CredConfig

from cloud_cert_renewer.config import Credentials


class AccessKeyCredentialProvider:
    """AccessKey credential provider (default method)"""

    def __init__(self, access_key_id: str, access_key_secret: str) -> None:
        """
        Initialize AccessKey credential provider
        :param access_key_id: AccessKey ID
        :param access_key_secret: AccessKey Secret
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret

    def get_credential_client(self) -> CredClient:
        """
        Get Alibaba Cloud Credentials client for AccessKey authentication
        :return: CredClient instance
        """
        config = CredConfig(
            type="access_key",
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
        )
        return CredClient(config)

    def get_credentials(self) -> Credentials:
        """Get AccessKey credentials"""
        return Credentials(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            security_token=None,
        )
