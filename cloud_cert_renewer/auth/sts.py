"""STS temporary credential provider

Provides credential retrieval based on STS temporary credentials.
"""

from alibabacloud_credentials.client import Client as CredClient
from alibabacloud_credentials.models import Config as CredConfig

from cloud_cert_renewer.config import Credentials


class STSCredentialProvider:
    """STS temporary credential provider"""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        security_token: str,
    ) -> None:
        """
        Initialize STS credential provider
        :param access_key_id: STS AccessKey ID
        :param access_key_secret: STS AccessKey Secret
        :param security_token: STS Security Token
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.security_token = security_token

    def get_credential_client(self) -> CredClient:
        """
        Get Alibaba Cloud Credentials client for STS authentication
        :return: CredClient instance
        """
        config = CredConfig(
            type="sts",
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            security_token=self.security_token,
        )
        return CredClient(config)

    def get_credentials(self) -> Credentials:
        """Get STS temporary credentials"""
        return Credentials(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            security_token=self.security_token,
        )
