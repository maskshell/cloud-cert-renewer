"""Authentication module

Provides abstract interfaces and implementations for various authentication methods,
supporting access_key, STS, IAM Role, OIDC (RRSA), Service Account, etc.
"""

from cloud_cert_renewer.auth.access_key import AccessKeyCredentialProvider
from cloud_cert_renewer.auth.base import CredentialProvider
from cloud_cert_renewer.auth.env import EnvCredentialProvider
from cloud_cert_renewer.auth.factory import CredentialProviderFactory
from cloud_cert_renewer.auth.iam_role import IAMRoleCredentialProvider
from cloud_cert_renewer.auth.oidc import OidcCredentialProvider
from cloud_cert_renewer.auth.service_account import ServiceAccountCredentialProvider
from cloud_cert_renewer.auth.sts import STSCredentialProvider

__all__ = [
    "AccessKeyCredentialProvider",
    "CredentialProvider",
    "CredentialProviderFactory",
    "EnvCredentialProvider",
    "IAMRoleCredentialProvider",
    "OidcCredentialProvider",
    "ServiceAccountCredentialProvider",
    "STSCredentialProvider",
]
