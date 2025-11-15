"""Tests for dependency injection container

Tests the Dependency Injection container implementation.
"""

import os
import sys
import unittest

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.container import (  # noqa: E402
    DIContainer,
    get_container,
    get_service,
    register_service,
)


class TestDIContainer(unittest.TestCase):
    """Dependency injection container tests"""

    def setUp(self):
        """Test setup"""
        self.container = DIContainer()

    def tearDown(self):
        """Test cleanup"""
        self.container.clear()

    def test_register_instance(self):
        """Test registering service instance"""
        test_instance = {"key": "value"}

        self.container.register("test_service", instance=test_instance)

        self.assertTrue(self.container.has("test_service"))
        result = self.container.get("test_service")
        self.assertEqual(result, test_instance)

    def test_register_factory(self):
        """Test registering service factory"""

        def factory():
            return {"created": "by_factory"}

        self.container.register("test_service", factory=factory)

        self.assertTrue(self.container.has("test_service"))
        result = self.container.get("test_service")
        self.assertIsInstance(result, dict)
        self.assertEqual(result["created"], "by_factory")

    def test_register_singleton(self):
        """Test registering singleton service"""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return {"id": call_count}

        self.container.register("test_service", factory=factory, singleton=True)

        # Get service multiple times
        instance1 = self.container.get("test_service")
        instance2 = self.container.get("test_service")
        instance3 = self.container.get("test_service")

        # Verify same instance is returned
        self.assertEqual(instance1, instance2)
        self.assertEqual(instance2, instance3)
        # Verify factory was called only once
        self.assertEqual(call_count, 1)

    def test_get_unregistered_service(self):
        """Test getting unregistered service raises error"""
        with self.assertRaises(KeyError) as context:
            self.container.get("unregistered_service")

        self.assertIn("Service not registered", str(context.exception))

    def test_has_service(self):
        """Test checking if service is registered"""
        self.assertFalse(self.container.has("test_service"))

        self.container.register("test_service", instance={"test": "value"})

        self.assertTrue(self.container.has("test_service"))

    def test_clear_container(self):
        """Test clearing container"""
        self.container.register("service1", instance={"key1": "value1"})
        self.container.register("service2", instance={"key2": "value2"})

        self.assertTrue(self.container.has("service1"))
        self.assertTrue(self.container.has("service2"))

        self.container.clear()

        self.assertFalse(self.container.has("service1"))
        self.assertFalse(self.container.has("service2"))

    def test_register_without_instance_or_factory(self):
        """Test registering without instance or factory raises error"""
        with self.assertRaises(ValueError) as context:
            self.container.register("test_service")

        self.assertIn("Must provide instance or factory", str(context.exception))


class TestGlobalContainerFunctions(unittest.TestCase):
    """Tests for global container functions"""

    def setUp(self):
        """Test setup"""
        # Clear global container
        container = get_container()
        container.clear()

    def tearDown(self):
        """Test cleanup"""
        container = get_container()
        container.clear()

    def test_register_service_global(self):
        """Test registering service to global container"""
        test_instance = {"key": "value"}

        register_service("test_service", instance=test_instance)

        result = get_service("test_service")
        self.assertEqual(result, test_instance)

    def test_get_service_global(self):
        """Test getting service from global container"""
        test_instance = {"key": "value"}

        register_service("test_service", instance=test_instance)

        result = get_service("test_service")
        self.assertEqual(result, test_instance)

    def test_get_container_returns_singleton(self):
        """Test get_container returns singleton instance"""
        container1 = get_container()
        container2 = get_container()

        self.assertIs(container1, container2)

    def test_register_service_singleton_global(self):
        """Test registering singleton service to global container"""
        call_count = 0

        def factory():
            nonlocal call_count
            call_count += 1
            return {"id": call_count}

        register_service("test_service", factory=factory, singleton=True)

        instance1 = get_service("test_service")
        instance2 = get_service("test_service")

        self.assertEqual(instance1, instance2)
        self.assertEqual(call_count, 1)


if __name__ == "__main__":
    unittest.main()
