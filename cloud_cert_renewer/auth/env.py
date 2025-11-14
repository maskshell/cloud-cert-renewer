"""环境变量凭证提供者

提供从环境变量读取凭证的功能。
"""

import os

from cloud_cert_renewer.config import Credentials
from cloud_cert_renewer.auth.base import CredentialProvider


class EnvCredentialProvider:
    """环境变量凭证提供者（从环境变量读取）"""

    def __init__(self) -> None:
        """初始化环境变量凭证提供者"""

    def get_credentials(self) -> Credentials:
        """
        从环境变量获取凭证
        支持的环境变量：
        - CLOUD_ACCESS_KEY_ID 或 ALIBABA_CLOUD_ACCESS_KEY_ID
        - CLOUD_ACCESS_KEY_SECRET 或 ALIBABA_CLOUD_ACCESS_KEY_SECRET
        - CLOUD_SECURITY_TOKEN（可选，用于STS）
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
                "缺少必要的环境变量: CLOUD_ACCESS_KEY_ID 或 CLOUD_ACCESS_KEY_SECRET"
            )

        return Credentials(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            security_token=security_token,
        )

