"""AccessKey凭证提供者

提供基于AccessKey ID和Secret的凭证获取。
"""

from cloud_cert_renewer.config import Credentials
from cloud_cert_renewer.auth.base import CredentialProvider


class AccessKeyCredentialProvider:
    """AccessKey凭证提供者（默认方式）"""

    def __init__(self, access_key_id: str, access_key_secret: str) -> None:
        """
        初始化AccessKey凭证提供者
        :param access_key_id: AccessKey ID
        :param access_key_secret: AccessKey Secret
        """
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret

    def get_credentials(self) -> Credentials:
        """获取AccessKey凭证"""
        return Credentials(
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            security_token=None,
        )

