"""鉴权模块

提供多种鉴权方式的抽象接口和实现，支持access_key、STS、IAM Role等。
"""

from cloud_cert_renewer.auth.access_key import AccessKeyCredentialProvider
from cloud_cert_renewer.auth.base import CredentialProvider
from cloud_cert_renewer.auth.env import EnvCredentialProvider
from cloud_cert_renewer.auth.factory import CredentialProviderFactory
from cloud_cert_renewer.auth.iam_role import IAMRoleCredentialProvider
from cloud_cert_renewer.auth.service_account import ServiceAccountCredentialProvider
from cloud_cert_renewer.auth.sts import STSCredentialProvider

__all__ = [
    "AccessKeyCredentialProvider",
    "CredentialProvider",
    "CredentialProviderFactory",
    "EnvCredentialProvider",
    "IAMRoleCredentialProvider",
    "ServiceAccountCredentialProvider",
    "STSCredentialProvider",
]

