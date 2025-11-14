"""AccessKey credential provider

Provides credential retrieval based on AccessKey ID and Secret.
"""

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

    def get_credentials(self) -> Credentials:
        """Get AccessKey credentials"""
        return Credentials(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            security_token=None,
        )
