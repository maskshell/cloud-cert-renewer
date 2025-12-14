"""Authentication provider base class

Defines abstract interface for authentication providers.
"""

from typing import TYPE_CHECKING, Protocol

from cloud_cert_renewer.config import Credentials

if TYPE_CHECKING:
    from alibabacloud_credentials.client import Client as CredClient


class CredentialProvider(Protocol):
    """Credential provider protocol interface"""

    def get_credential_client(self) -> "CredClient":
        """
        Get Alibaba Cloud Credentials client
        :return: CredClient instance for SDK authentication
        """
        ...

    def get_credentials(self) -> Credentials:
        """
        Get credentials
        :return: Credentials object
        :raises ValueError: When credentials cannot be obtained
        """
        ...
