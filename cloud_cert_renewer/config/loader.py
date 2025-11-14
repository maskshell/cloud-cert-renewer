"""配置加载器

从环境变量加载配置，支持新旧环境变量名称回退。
"""

import logging
import os

from dotenv import load_dotenv

from cloud_cert_renewer.config.models import (
    AppConfig,
    CdnConfig,
    Credentials,
    LoadBalancerConfig,
)

logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """配置错误异常"""

    pass


def _get_env_with_fallback(new_name: str, old_name: str | None = None) -> str | None:
    """获取环境变量，支持新旧名称回退"""
    value = os.environ.get(new_name)
    if value:
        return value
    if old_name:
        old_value = os.environ.get(old_name)
        if old_value:
            logger.warning("环境变量 %s 已弃用，请使用 %s 替代", old_name, new_name)
            return old_value
    return None


def _get_env_required(
    new_name: str, old_name: str | None = None, error_msg: str | None = None
) -> str:
    """获取必需的环境变量，支持新旧名称回退"""
    value = _get_env_with_fallback(new_name, old_name)
    if not value:
        if error_msg:
            raise ConfigError(error_msg)
        raise ConfigError(f"缺少必要的环境变量: {new_name}")
    return value


def _parse_bool_env(env_name: str, default: bool = False) -> bool:
    """解析布尔型环境变量"""
    value = os.environ.get(env_name, "").lower()
    return value in ("true", "1", "yes", "on")


def load_config() -> AppConfig:
    """
    从环境变量加载配置
    支持新旧环境变量名称，优先使用新名称
    :return: AppConfig配置对象
    :raises ConfigError: 配置错误时抛出
    """
    # 加载 .env 文件
    load_dotenv()

    # 获取服务类型（支持新旧名称）
    service_type_str = _get_env_with_fallback("SERVICE_TYPE") or "cdn"
    service_type = service_type_str.lower()

    # 向后兼容：slb -> lb
    if service_type == "slb":
        logger.warning("SERVICE_TYPE=slb 已弃用，请使用 SERVICE_TYPE=lb")
        service_type = "lb"

    if service_type not in ["cdn", "lb"]:
        raise ConfigError(f"不支持的服务类型: {service_type}，仅支持 cdn 或 lb")

    # 获取云服务提供商（默认alibaba，向后兼容）
    cloud_provider = (_get_env_with_fallback("CLOUD_PROVIDER") or "alibaba").lower()

    # 获取鉴权方式（默认access_key）
    auth_method = (_get_env_with_fallback("AUTH_METHOD") or "access_key").lower()

    # 获取访问凭证（支持新旧名称）
    access_key_id = _get_env_required(
        "CLOUD_ACCESS_KEY_ID",
        "ALIBABA_CLOUD_ACCESS_KEY_ID",
        "缺少必要的环境变量: CLOUD_ACCESS_KEY_ID 或 ALIBABA_CLOUD_ACCESS_KEY_ID",
    )
    access_key_secret = _get_env_required(
        "CLOUD_ACCESS_KEY_SECRET",
        "ALIBABA_CLOUD_ACCESS_KEY_SECRET",
        "缺少必要的环境变量: CLOUD_ACCESS_KEY_SECRET 或 ALIBABA_CLOUD_ACCESS_KEY_SECRET",
    )

    # STS临时凭证（可选）
    security_token = _get_env_with_fallback("CLOUD_SECURITY_TOKEN")

    credentials = Credentials(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        security_token=security_token,
    )

    # 获取强制更新标志
    force_update = _parse_bool_env("FORCE_UPDATE", False)

    # 根据服务类型获取不同的配置
    if service_type == "cdn":
        domain_name = _get_env_required(
            "CDN_DOMAIN_NAME",
            error_msg="缺少必要的环境变量: CDN_DOMAIN_NAME",
        )
        cert = _get_env_required("CDN_CERT", error_msg="缺少必要的环境变量: CDN_CERT")
        cert_private_key = _get_env_required(
            "CDN_CERT_PRIVATE_KEY",
            error_msg="缺少必要的环境变量: CDN_CERT_PRIVATE_KEY",
        )
        region = _get_env_with_fallback("CDN_REGION") or "cn-hangzhou"

        cdn_config = CdnConfig(
            domain_name=domain_name,
            cert=cert,
            cert_private_key=cert_private_key,
            region=region,
        )

        return AppConfig(
            service_type="cdn",
            cloud_provider=cloud_provider,
            auth_method=auth_method,
            credentials=credentials,
            force_update=force_update,
            cdn_config=cdn_config,
        )

    elif service_type == "lb":
        instance_id = _get_env_required(
            "LB_INSTANCE_ID",
            "SLB_INSTANCE_ID",
            "缺少必要的环境变量: LB_INSTANCE_ID 或 SLB_INSTANCE_ID",
        )
        listener_port_str = _get_env_required(
            "LB_LISTENER_PORT",
            "SLB_LISTENER_PORT",
            "缺少必要的环境变量: LB_LISTENER_PORT 或 SLB_LISTENER_PORT",
        )
        cert = _get_env_required(
            "LB_CERT",
            "SLB_CERT",
            "缺少必要的环境变量: LB_CERT 或 SLB_CERT",
        )
        cert_private_key = _get_env_required(
            "LB_CERT_PRIVATE_KEY",
            "SLB_CERT_PRIVATE_KEY",
            "缺少必要的环境变量: LB_CERT_PRIVATE_KEY 或 SLB_CERT_PRIVATE_KEY",
        )
        region = _get_env_with_fallback("LB_REGION", "SLB_REGION") or "cn-hangzhou"

        try:
            listener_port = int(listener_port_str)
            if listener_port < 1 or listener_port > 65535:
                raise ConfigError(
                    f"LB_LISTENER_PORT 必须在 1-65535 之间: {listener_port}"
                )
        except ValueError as e:
            raise ConfigError(
                f"LB_LISTENER_PORT 必须是有效的整数: {listener_port_str}"
            ) from e

        lb_config = LoadBalancerConfig(
            instance_id=instance_id,
            listener_port=listener_port,
            cert=cert,
            cert_private_key=cert_private_key,
            region=region,
        )

        return AppConfig(
            service_type="lb",
            cloud_provider=cloud_provider,
            auth_method=auth_method,
            credentials=credentials,
            force_update=force_update,
            lb_config=lb_config,
        )

    else:
        # 理论上不应该到达这里
        raise ConfigError(f"不支持的服务类型: {service_type}，仅支持 cdn 或 lb")

