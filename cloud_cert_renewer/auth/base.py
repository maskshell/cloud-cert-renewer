"""Authentication provider base class

Defines abstract interface for authentication providers.
"""

from typing import Protocol

from cloud_cert_renewer.config import Credentials


class CredentialProvider(Protocol):
    """Credential provider protocol interface"""

    def get_credentials(self) -> Credentials:
        """
        Get credentials
        :return: Credentials object
        :raises ValueError: When credentials cannot be obtained
        """
        ...  # noqa: UP007
