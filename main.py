import logging
import sys

from cloud_cert_renewer.cert_renewer import (
    CertRenewerFactory,
    CertValidationError,
)
from cloud_cert_renewer.config import ConfigError, load_config
from cloud_cert_renewer.container import get_container, register_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# CdnCertRenewer and LoadBalancerCertRenewer have been moved to
# cloud_cert_renewer.clients.alibaba module


def main() -> None:
    """
    Main function: Update CDN or Load Balancer certificate based on configuration
    """
    try:
        # Load configuration
        config = load_config()

        # Register configuration to dependency injection container
        container = get_container()
        register_service("config", instance=config, singleton=True)

        # Register certificate renewer factory
        register_service(
            "cert_renewer_factory",
            instance=CertRenewerFactory,
            singleton=True,
        )

        logger.info(
            "Starting certificate renewal: service_type=%s, "
            "cloud_provider=%s, auth_method=%s, region=%s, force_update=%s",
            config.service_type,
            config.cloud_provider,
            config.auth_method,
            (
                config.cdn_config.region
                if config.cdn_config
                else config.lb_config.region
                if config.lb_config
                else "unknown"
            ),
            config.force_update,
        )

        # Get certificate renewer factory from dependency injection container
        factory = container.get("cert_renewer_factory")
        renewer = factory.create(config)
        success = renewer.renew()

        if success:
            logger.info("Certificate renewal completed")
            sys.exit(0)
        else:
            logger.error("Certificate renewal failed")
            sys.exit(1)

    except ConfigError as e:
        logger.error("Configuration error: %s", e)
        sys.exit(1)
    except CertValidationError as e:
        logger.error("Certificate validation error: %s", e)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        # Main function needs to catch all exceptions to ensure graceful exit
        logger.exception("Unexpected error occurred: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
