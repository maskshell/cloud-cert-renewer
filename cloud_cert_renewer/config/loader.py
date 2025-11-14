"""Configuration loader

Loads configuration from environment variables, supports fallback for old and new environment variable names.
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
    """Configuration error exception"""

    pass


def _get_env_with_fallback(new_name: str, old_name: str | None = None) -> str | None:
    """Get environment variable with fallback support for old and new names"""
    value = os.environ.get(new_name)
    if value:
        return value
    if old_name:
        old_value = os.environ.get(old_name)
        if old_value:
            logger.warning(
                "Environment variable %s is deprecated, please use %s instead",
                old_name,
                new_name,
            )
            return old_value
    return None


def _get_env_required(
    new_name: str, old_name: str | None = None, error_msg: str | None = None
) -> str:
    """Get required environment variable with fallback support for old and new names"""
    value = _get_env_with_fallback(new_name, old_name)
    if not value:
        if error_msg:
            raise ConfigError(error_msg)
        raise ConfigError(f"Missing required environment variable: {new_name}")
    return value


def _parse_bool_env(env_name: str, default: bool = False) -> bool:
    """Parse boolean environment variable"""
    value = os.environ.get(env_name, "").lower()
    return value in ("true", "1", "yes", "on")


def load_config() -> AppConfig:
    """
    Load configuration from environment variables
    Supports old and new environment variable names, prioritizing new names
    :return: AppConfig configuration object
    :raises ConfigError: Raises when configuration error occurs
    """
    # Load .env file
    load_dotenv()

    # Get service type (supports old and new names)
    service_type_str = _get_env_with_fallback("SERVICE_TYPE") or "cdn"
    service_type = service_type_str.lower()

    # Backward compatibility: slb -> lb
    if service_type == "slb":
        logger.warning("SERVICE_TYPE=slb is deprecated, please use SERVICE_TYPE=lb")
        service_type = "lb"

    if service_type not in ["cdn", "lb"]:
        raise ConfigError(
            f"Unsupported service type: {service_type}, only cdn or lb are supported"
        )

    # Get cloud provider (default alibaba, backward compatible)
    cloud_provider = (_get_env_with_fallback("CLOUD_PROVIDER") or "alibaba").lower()

    # Get authentication method (default access_key)
    auth_method = (_get_env_with_fallback("AUTH_METHOD") or "access_key").lower()

    # Get access credentials (supports old and new names)
    access_key_id = _get_env_required(
        "CLOUD_ACCESS_KEY_ID",
        "ALIBABA_CLOUD_ACCESS_KEY_ID",
        "Missing required environment variable: CLOUD_ACCESS_KEY_ID or ALIBABA_CLOUD_ACCESS_KEY_ID",
    )
    access_key_secret = _get_env_required(
        "CLOUD_ACCESS_KEY_SECRET",
        "ALIBABA_CLOUD_ACCESS_KEY_SECRET",
        "Missing required environment variable: CLOUD_ACCESS_KEY_SECRET or ALIBABA_CLOUD_ACCESS_KEY_SECRET",
    )

    # STS temporary credentials (optional)
    security_token = _get_env_with_fallback("CLOUD_SECURITY_TOKEN")

    credentials = Credentials(
        access_key_id=access_key_id,
        access_key_secret=access_key_secret,
        security_token=security_token,
    )

    # Get force update flag
    force_update = _parse_bool_env("FORCE_UPDATE", False)

    # Get different configurations based on service type
    if service_type == "cdn":
        domain_name = _get_env_required(
            "CDN_DOMAIN_NAME",
            error_msg="Missing required environment variable: CDN_DOMAIN_NAME",
        )
        cert = _get_env_required(
            "CDN_CERT", error_msg="Missing required environment variable: CDN_CERT"
        )
        cert_private_key = _get_env_required(
            "CDN_CERT_PRIVATE_KEY",
            error_msg="Missing required environment variable: CDN_CERT_PRIVATE_KEY",
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
            "Missing required environment variable: LB_INSTANCE_ID or SLB_INSTANCE_ID",
        )
        listener_port_str = _get_env_required(
            "LB_LISTENER_PORT",
            "SLB_LISTENER_PORT",
            "Missing required environment variable: LB_LISTENER_PORT or SLB_LISTENER_PORT",
        )
        cert = _get_env_required(
            "LB_CERT",
            "SLB_CERT",
            "Missing required environment variable: LB_CERT or SLB_CERT",
        )
        cert_private_key = _get_env_required(
            "LB_CERT_PRIVATE_KEY",
            "SLB_CERT_PRIVATE_KEY",
            "Missing required environment variable: LB_CERT_PRIVATE_KEY or SLB_CERT_PRIVATE_KEY",
        )
        region = _get_env_with_fallback("LB_REGION", "SLB_REGION") or "cn-hangzhou"

        try:
            listener_port = int(listener_port_str)
            if listener_port < 1 or listener_port > 65535:
                raise ConfigError(
                    f"LB_LISTENER_PORT must be between 1-65535: {listener_port}"
                )
        except ValueError as e:
            raise ConfigError(
                f"LB_LISTENER_PORT must be a valid integer: {listener_port_str}"
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
        # Should not reach here in theory
        raise ConfigError(
            f"Unsupported service type: {service_type}, only cdn or lb are supported"
        )
