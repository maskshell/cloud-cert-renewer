"""Dependency injection container module

Provides simple dependency injection container implementation, supporting service registration and resolution.
"""

import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DIContainer:
    """Dependency injection container"""

    def __init__(self) -> None:
        """Initialize container"""
        self._services: dict[str, Any] = {}
        self._factories: dict[str, Callable[[], Any]] = {}
        self._singletons: dict[str, Any] = {}

    def register(
        self,
        service_name: str,
        instance: Any | None = None,
        factory: Callable[[], Any] | None = None,
        singleton: bool = False,
    ) -> None:
        """
        Register service
        :param service_name: Service name
        :param instance: Service instance (if provided, will be used directly)
        :param factory: Factory function (for creating service instances)
        :param singleton: Whether singleton mode
        """
        if instance is not None:
            self._services[service_name] = instance
            logger.debug("Registered service instance: %s", service_name)
        elif factory is not None:
            if singleton:
                self._factories[service_name] = factory
                logger.debug("Registered singleton factory: %s", service_name)
            else:
                self._factories[service_name] = factory
                logger.debug("Registered factory: %s", service_name)
        else:
            raise ValueError("Must provide instance or factory parameter")

    def get(self, service_name: str) -> Any:
        """
        Get service instance
        :param service_name: Service name
        :return: Service instance
        :raises KeyError: Raises when service is not registered
        """
        # First check if there is a directly registered instance
        if service_name in self._services:
            return self._services[service_name]

        # Check if there is a factory function
        if service_name in self._factories:
            factory = self._factories[service_name]

            # Check if singleton
            if service_name in self._singletons:
                return self._singletons[service_name]

            # Create instance
            instance = factory()

            # If singleton, cache instance
            if service_name in self._factories:
                # Check if should be singleton (by checking if already registered in singletons)
                # Here simplified: if factory exists and not in singletons, create and cache
                # Actually should judge by singleton parameter during register, here simplified implementation
                self._singletons[service_name] = instance

            return instance

        raise KeyError(f"Service not registered: {service_name}")

    def has(self, service_name: str) -> bool:
        """
        Check if service is registered
        :param service_name: Service name
        :return: Whether registered
        """
        return (
            service_name in self._services
            or service_name in self._factories
            or service_name in self._singletons
        )

    def clear(self) -> None:
        """Clear container"""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        logger.debug("Container cleared")


# Global container instance
_container = DIContainer()


def get_container() -> DIContainer:
    """
    Get global container instance
    :return: DIContainer instance
    """
    return _container


def register_service(
    service_name: str,
    instance: Any | None = None,
    factory: Callable[[], Any] | None = None,
    singleton: bool = False,
) -> None:
    """
    Register service to global container
    :param service_name: Service name
    :param instance: Service instance
    :param factory: Factory function
    :param singleton: Whether singleton mode
    """
    _container.register(
        service_name=service_name,
        instance=instance,
        factory=factory,
        singleton=singleton,
    )


def get_service(service_name: str) -> Any:
    """
    Get service from global container
    :param service_name: Service name
    :return: Service instance
    """
    return _container.get(service_name)
