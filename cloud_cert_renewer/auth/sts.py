"""STS临时凭证提供者

提供基于STS临时凭证的凭证获取。
"""

from cloud_cert_renewer.config import Credentials
from cloud_cert_renewer.auth.base import CredentialProvider


class STSCredentialProvider:
    """STS临时凭证提供者"""

    def __init__(
        self,
        access_key_id: str,
        access_key_secret: str,
        security_token: str,
    ) -> None:
        """
        初始化STS凭证提供者
        :param access_key_id: STS AccessKey ID
        :param access_key_secret: STS AccessKey Secret
        :param security_token: STS Security Token
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.security_token = security_token

    def get_credentials(self) -> Credentials:
        """获取STS临时凭证"""
        return Credentials(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            security_token=self.security_token,
        )

