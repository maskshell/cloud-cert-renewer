"""Environment variable credential provider

Provides functionality to read credentials from environment variables.
"""

import os

from alibabacloud_credentials.client import Client as CredClient
from alibabacloud_credentials.models import Config as CredConfig

from cloud_cert_renewer.config import Credentials


class EnvCredentialProvider:
    """Environment variable credential provider (reads from environment variables)"""

    def __init__(self) -> None:
        """Initialize environment variable credential provider"""

    def get_credential_client(self) -> CredClient:
        """
        Get Alibaba Cloud Credentials client based on available environment variables
        Supports access_key, sts, or uses default credential chain
        :return: CredClient instance
        """
        access_key_id = os.environ.get("CLOUD_ACCESS_KEY_ID") or os.environ.get(
            "ALIBABA_CLOUD_ACCESS_KEY_ID"
        )
        access_key_secret = os.environ.get("CLOUD_ACCESS_KEY_SECRET") or os.environ.get(
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET"
        )
        security_token = os.environ.get("CLOUD_SECURITY_TOKEN")

        if access_key_id and access_key_secret:
            if security_token:
                # STS credentials
                config = CredConfig(
                    type="sts",
                    access_key_id=access_key_id,
                    access_key_secret=access_key_secret,
                    security_token=security_token,
                )
            else:
                # AccessKey credentials
                config = CredConfig(
                    type="access_key",
                    access_key_id=access_key_id,
                    access_key_secret=access_key_secret,
                )
            return CredClient(config)

        # Use default credential chain (will try ECS RAM role, etc.)
        return CredClient()

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
