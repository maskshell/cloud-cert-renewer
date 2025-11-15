"""Credential provider factory

Provides creation logic for credential providers.
"""

from cloud_cert_renewer.auth.access_key import AccessKeyCredentialProvider
from cloud_cert_renewer.auth.base import CredentialProvider
from cloud_cert_renewer.auth.env import EnvCredentialProvider
from cloud_cert_renewer.auth.iam_role import IAMRoleCredentialProvider
from cloud_cert_renewer.auth.oidc import OidcCredentialProvider
from cloud_cert_renewer.auth.service_account import ServiceAccountCredentialProvider
from cloud_cert_renewer.auth.sts import STSCredentialProvider
from cloud_cert_renewer.config import Credentials


class CredentialProviderFactory:
    """Credential provider factory"""

    @staticmethod
    def create(
        auth_method: str,
        credentials: Credentials | None = None,
        **kwargs,
    ) -> CredentialProvider:
        """
        Create credential provider
        :param auth_method: Authentication method
            (access_key, sts, iam_role, oidc, service_account, env)
        :param credentials: Existing credentials object (optional)
        :param kwargs: Other parameters
        :return: CredentialProvider instance
        :raises ValueError: Raises when auth_method is not supported
        """
        auth_method = auth_method.lower()

        if auth_method == "access_key":
            if credentials:
                return AccessKeyCredentialProvider(
                    access_key_id=credentials.access_key_id,
                    access_key_secret=credentials.access_key_secret,
                )
            # Get from kwargs
            access_key_id = kwargs.get("access_key_id")
            access_key_secret = kwargs.get("access_key_secret")
            if not access_key_id or not access_key_secret:
                raise ValueError(
                    "access_key authentication method requires "
                    "access_key_id and access_key_secret"
                )
            return AccessKeyCredentialProvider(
                access_key_id=access_key_id, access_key_secret=access_key_secret
            )

        elif auth_method == "sts":
            if credentials and credentials.security_token:
                return STSCredentialProvider(
                    access_key_id=credentials.access_key_id,
                    access_key_secret=credentials.access_key_secret,
                    security_token=credentials.security_token,
                )
            # Get from kwargs
            access_key_id = kwargs.get("access_key_id")
            access_key_secret = kwargs.get("access_key_secret")
            security_token = kwargs.get("security_token")
            if not access_key_id or not access_key_secret or not security_token:
                raise ValueError(
                    "sts authentication method requires access_key_id, "
                    "access_key_secret and security_token"
                )
            return STSCredentialProvider(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                security_token=security_token,
            )

        elif auth_method == "iam_role":
            role_arn = kwargs.get("role_arn")
            if not role_arn:
                raise ValueError("iam_role authentication method requires role_arn")
            role_session_name = kwargs.get("role_session_name")
            return IAMRoleCredentialProvider(
                role_arn=role_arn, role_session_name=role_session_name
            )

        elif auth_method == "service_account":
            service_account_path = kwargs.get(
                "service_account_path",
                "/var/run/secrets/kubernetes.io/serviceaccount",
            )
            return ServiceAccountCredentialProvider(
                service_account_path=service_account_path
            )

        elif auth_method == "oidc":
            # OIDC parameters are read from environment variables
            # (injected by Kubernetes)
            # Optional kwargs for override
            role_arn = kwargs.get("role_arn")
            oidc_provider_arn = kwargs.get("oidc_provider_arn")
            oidc_token_file_path = kwargs.get("oidc_token_file_path")
            role_session_name = kwargs.get("role_session_name")
            return OidcCredentialProvider(
                role_arn=role_arn,
                oidc_provider_arn=oidc_provider_arn,
                oidc_token_file_path=oidc_token_file_path,
                role_session_name=role_session_name,
            )

        elif auth_method == "env":
            return EnvCredentialProvider()

        else:
            raise ValueError(
                f"Unsupported authentication method: {auth_method}, "
                f"supported methods: access_key, sts, iam_role, oidc, "
                f"service_account, env"
            )
