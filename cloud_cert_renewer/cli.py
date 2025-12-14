from __future__ import annotations

import logging
from enum import IntEnum

from cloud_cert_renewer.auth.errors import AuthError
from cloud_cert_renewer.cert_renewer import (
    CertRenewerFactory,
    CertValidationError,
)
from cloud_cert_renewer.config import ConfigError, load_config
from cloud_cert_renewer.container import get_container, register_service
from cloud_cert_renewer.errors import (
    CloudApiError,
    UnsupportedCloudProviderError,
    UnsupportedServiceTypeError,
)
from cloud_cert_renewer.logging_utils import configure_logging

logger = logging.getLogger(__name__)


class ExitCode(IntEnum):
    SUCCESS = 0
    FAILURE = 1
    CONFIG_ERROR = 2
    CERT_VALIDATION_ERROR = 3
    AUTH_ERROR = 4
    UNSUPPORTED = 5
    NOT_IMPLEMENTED = 6
    CLOUD_API_ERROR = 7


def run() -> int:
    configure_logging()

    try:
        config = load_config()

        container = get_container()
        register_service("config", instance=config, singleton=True)
        register_service(
            "cert_renewer_factory",
            instance=CertRenewerFactory,
            singleton=True,
        )

        logger.info(
            "Starting certificate renewal: service_type=%s, cloud_provider=%s, "
            "auth_method=%s, force_update=%s",
            config.service_type,
            config.cloud_provider,
            config.auth_method,
            config.force_update,
        )

        factory = container.get("cert_renewer_factory")
        renewer = factory.create(config)
        success = renewer.renew()

        if success:
            logger.info("Certificate renewal completed")
            return int(ExitCode.SUCCESS)

        logger.error("Certificate renewal failed")
        return int(ExitCode.FAILURE)

    except ConfigError as e:
        logger.error("Configuration error: %s", e)
        return int(ExitCode.CONFIG_ERROR)
    except CertValidationError as e:
        logger.error("Certificate validation error: %s", e)
        return int(ExitCode.CERT_VALIDATION_ERROR)
    except AuthError as e:
        logger.error("Authentication error: %s", e)
        return int(ExitCode.AUTH_ERROR)
    except CloudApiError as e:
        logger.error("Cloud API error: %s", e)
        return int(ExitCode.CLOUD_API_ERROR)
    except (UnsupportedCloudProviderError, UnsupportedServiceTypeError) as e:
        logger.error("Unsupported operation: %s", e)
        return int(ExitCode.UNSUPPORTED)
    except NotImplementedError as e:
        logger.error("Not implemented: %s", e)
        return int(ExitCode.NOT_IMPLEMENTED)
    except ValueError as e:
        logger.error("Invalid value: %s", e)
        return int(ExitCode.CONFIG_ERROR)
    except Exception as e:  # noqa: BLE001
        logger.exception("Unexpected error occurred: %s", e)
        return int(ExitCode.FAILURE)


def main() -> None:
    raise SystemExit(run())
