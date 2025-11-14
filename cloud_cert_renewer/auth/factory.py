"""凭证提供者工厂

提供凭证提供者的创建逻辑。
"""

from cloud_cert_renewer.auth.access_key import AccessKeyCredentialProvider
from cloud_cert_renewer.auth.base import CredentialProvider
from cloud_cert_renewer.auth.env import EnvCredentialProvider
from cloud_cert_renewer.auth.iam_role import IAMRoleCredentialProvider
from cloud_cert_renewer.auth.service_account import ServiceAccountCredentialProvider
from cloud_cert_renewer.auth.sts import STSCredentialProvider
from cloud_cert_renewer.config import Credentials


class CredentialProviderFactory:
    """凭证提供者工厂"""

    @staticmethod
    def create(
        auth_method: str,
        credentials: Credentials | None = None,
        **kwargs,
    ) -> CredentialProvider:
        """
        创建凭证提供者
        :param auth_method: 鉴权方式（access_key, sts, iam_role, service_account, env）
        :param credentials: 已有的凭证对象（可选）
        :param kwargs: 其他参数
        :return: CredentialProvider实例
        :raises ValueError: 当auth_method不支持时抛出
        """
        auth_method = auth_method.lower()

        if auth_method == "access_key":
            if credentials:
                return AccessKeyCredentialProvider(
                    access_key_id=credentials.access_key_id,
                    access_key_secret=credentials.access_key_secret,
                )
            # 从kwargs获取
            access_key_id = kwargs.get("access_key_id")
            access_key_secret = kwargs.get("access_key_secret")
            if not access_key_id or not access_key_secret:
                raise ValueError(
                    "access_key鉴权方式需要提供access_key_id和access_key_secret"
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
            # 从kwargs获取
            access_key_id = kwargs.get("access_key_id")
            access_key_secret = kwargs.get("access_key_secret")
            security_token = kwargs.get("security_token")
            if not access_key_id or not access_key_secret or not security_token:
                raise ValueError(
                    "sts鉴权方式需要提供access_key_id、access_key_secret和security_token"
                )
            return STSCredentialProvider(
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                security_token=security_token,
            )

        elif auth_method == "iam_role":
            role_arn = kwargs.get("role_arn")
            if not role_arn:
                raise ValueError("iam_role鉴权方式需要提供role_arn")
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

        elif auth_method == "env":
            return EnvCredentialProvider()

        else:
            raise ValueError(
                f"不支持的鉴权方式: {auth_method}，"
                f"支持的方式: access_key, sts, iam_role, service_account, env"
            )

