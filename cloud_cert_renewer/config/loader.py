"""Configuration loader

Loads configuration from environment variables, supports fallback for old and
new environment variable names.
"""

import argparse
import logging
import os

from dotenv import load_dotenv

from cloud_cert_renewer.config.models import (
    AppConfig,
    CdnConfig,
    Credentials,
    LoadBalancerConfig,
    WebhookConfig,
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


def _parse_int_env(env_name: str, default: int) -> int:
    """Parse integer environment variable"""
    value = os.environ.get(env_name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        logger.warning(
            "Invalid integer value for %s: %s, using default: %d",
            env_name,
            value,
            default,
        )
        return default


def _parse_float_env(env_name: str, default: float) -> float:
    """Parse float environment variable"""
    value = os.environ.get(env_name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        logger.warning(
            "Invalid float value for %s: %s, using default: %f",
            env_name,
            value,
            default,
        )
        return default


def load_config(args: argparse.Namespace | None = None) -> AppConfig:
    """
    Load configuration from environment variables
    Supports old and new environment variable names, prioritizing new names
    :param args: Optional command-line arguments
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

    # Credentials requirements depend on auth_method.
    # Some auth methods (e.g., env, oidc, service_account) do not require
    # explicit AccessKey values at config-load time.
    if auth_method in {"access_key", "sts"}:
        access_key_id = _get_env_required(
            "CLOUD_ACCESS_KEY_ID",
            "ALIBABA_CLOUD_ACCESS_KEY_ID",
            "Missing required environment variable: "
            "CLOUD_ACCESS_KEY_ID or ALIBABA_CLOUD_ACCESS_KEY_ID",
        )
        access_key_secret = _get_env_required(
            "CLOUD_ACCESS_KEY_SECRET",
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET",
            "Missing required environment variable: "
            "CLOUD_ACCESS_KEY_SECRET or ALIBABA_CLOUD_ACCESS_KEY_SECRET",
        )

        security_token = _get_env_with_fallback("CLOUD_SECURITY_TOKEN")
        if auth_method == "sts" and not security_token:
            raise ConfigError(
                "Missing required environment variable: CLOUD_SECURITY_TOKEN "
                "(required when AUTH_METHOD=sts)"
            )

        credentials = Credentials(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
            security_token=security_token,
        )
    elif auth_method == "iam_role":
        # IAM role auth can read base credentials from environment at runtime.
        # If AccessKey values are provided, keep them to avoid additional env reads.
        access_key_id = _get_env_with_fallback(
            "CLOUD_ACCESS_KEY_ID", "ALIBABA_CLOUD_ACCESS_KEY_ID"
        )
        access_key_secret = _get_env_with_fallback(
            "CLOUD_ACCESS_KEY_SECRET", "ALIBABA_CLOUD_ACCESS_KEY_SECRET"
        )
        credentials = Credentials(
            access_key_id=access_key_id or "",
            access_key_secret=access_key_secret or "",
            security_token=None,
        )
    else:
        # Placeholder credentials; actual credentials may be resolved at runtime
        # by the selected CredentialProvider (e.g., OIDC/RRSA, env chain, etc.).
        credentials = Credentials(
            access_key_id="",
            access_key_secret="",
            security_token=None,
        )

    # Get force update flag
    force_update = _parse_bool_env("FORCE_UPDATE", False)

    # Get dry_run from args if available
    dry_run = False
    if args and hasattr(args, "dry_run"):
        dry_run = args.dry_run

    # Load webhook configuration
    webhook_url = _get_env_with_fallback("WEBHOOK_URL")
    webhook_config = None
    if webhook_url:
        logger.info("Webhook URL found in environment variables")
        webhook_timeout = _parse_int_env("WEBHOOK_TIMEOUT", 30)
        webhook_retry_attempts = _parse_int_env("WEBHOOK_RETRY_ATTEMPTS", 3)
        webhook_retry_delay = _parse_float_env("WEBHOOK_RETRY_DELAY", 1.0)

        # Parse enabled events
        webhook_enabled_events_str = _get_env_with_fallback("WEBHOOK_ENABLED_EVENTS")
        webhook_enabled_events = None
        if webhook_enabled_events_str:
            webhook_enabled_events = {
                event.strip()
                for event in webhook_enabled_events_str.split(",")
                if event.strip()
            }

        # Get message format (default: generic)
        webhook_message_format = (
            _get_env_with_fallback("WEBHOOK_MESSAGE_FORMAT") or "generic"
        ).lower()

        webhook_config = WebhookConfig(
            url=webhook_url,
            timeout=webhook_timeout,
            retry_attempts=webhook_retry_attempts,
            retry_delay=webhook_retry_delay,
            enabled_events=webhook_enabled_events
            or {
                "renewal_started",
                "renewal_success",
                "renewal_failed",
                "renewal_skipped",
                "batch_completed",
            },
            message_format=webhook_message_format,
        )
    else:
        logger.debug(
            "Webhook URL not found in environment variables "
            "(WEBHOOK_URL is not set or empty)"
        )

    # Get different configurations based on service type
    if service_type == "cdn":
        domain_name_str = _get_env_required(
            "CDN_DOMAIN_NAME",
            error_msg="Missing required environment variable: CDN_DOMAIN_NAME",
        )
        domain_names = [d.strip() for d in domain_name_str.split(",") if d.strip()]

        cert = _get_env_required(
            "CDN_CERT", error_msg="Missing required environment variable: CDN_CERT"
        )
        cert_private_key = _get_env_required(
            "CDN_CERT_PRIVATE_KEY",
            error_msg="Missing required environment variable: CDN_CERT_PRIVATE_KEY",
        )
        region = _get_env_with_fallback("CDN_REGION") or "cn-hangzhou"

        cdn_config = CdnConfig(
            domain_names=domain_names,
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
            dry_run=dry_run,
            cdn_config=cdn_config,
            webhook_config=webhook_config,
        )

    elif service_type == "lb":
        instance_id_str = _get_env_required(
            "LB_INSTANCE_ID",
            "SLB_INSTANCE_ID",
            "Missing required environment variable: LB_INSTANCE_ID or SLB_INSTANCE_ID",
        )
        instance_ids = [i.strip() for i in instance_id_str.split(",") if i.strip()]

        listener_port_str = _get_env_required(
            "LB_LISTENER_PORT",
            "SLB_LISTENER_PORT",
            "Missing required environment variable: "
            "LB_LISTENER_PORT or SLB_LISTENER_PORT",
        )
        cert = _get_env_required(
            "LB_CERT",
            "SLB_CERT",
            "Missing required environment variable: LB_CERT or SLB_CERT",
        )
        cert_private_key = _get_env_required(
            "LB_CERT_PRIVATE_KEY",
            "SLB_CERT_PRIVATE_KEY",
            "Missing required environment variable: "
            "LB_CERT_PRIVATE_KEY or SLB_CERT_PRIVATE_KEY",
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
            instance_ids=instance_ids,
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
            dry_run=dry_run,
            lb_config=lb_config,
            webhook_config=webhook_config,
        )

    else:
        # Should not reach here in theory
        raise ConfigError(
            f"Unsupported service type: {service_type}, only cdn or lb are supported"
        )
