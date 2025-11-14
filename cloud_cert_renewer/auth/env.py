"""Environment variable credential provider

Provides functionality to read credentials from environment variables.
"""

import os

from cloud_cert_renewer.config import Credentials


class EnvCredentialProvider:
    """Environment variable credential provider (reads from environment variables)"""

    def __init__(self) -> None:
        """Initialize environment variable credential provider"""

    def get_credentials(self) -> Credentials:
        """
        Get credentials from environment variables
        Supported environment variables:
        - CLOUD_ACCESS_KEY_ID or ALIBABA_CLOUD_ACCESS_KEY_ID
        - CLOUD_ACCESS_KEY_SECRET or ALIBABA_CLOUD_ACCESS_KEY_SECRET
        - CLOUD_SECURITY_TOKEN (optional, for STS)
        """
        access_key_id = os.environ.get("CLOUD_ACCESS_KEY_ID") or os.environ.get(
            "ALIBABA_CLOUD_ACCESS_KEY_ID"
        )
        access_key_secret = os.environ.get("CLOUD_ACCESS_KEY_SECRET") or os.environ.get(
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET"
        )
        security_token = os.environ.get("CLOUD_SECURITY_TOKEN")

        if not access_key_id or not access_key_secret:
            raise ValueError(
                "Missing required environment variables: "
                "CLOUD_ACCESS_KEY_ID or CLOUD_ACCESS_KEY_SECRET"
            )

        return Credentials(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            security_token=security_token,
        )
