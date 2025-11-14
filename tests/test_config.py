"""Tests for configuration module

Tests the configuration loading and validation logic.
"""

import os
import sys
import unittest

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.config import ConfigError, load_config
from cloud_cert_renewer.config.models import (
    AppConfig,
    CdnConfig,
    Credentials,
    LoadBalancerConfig,
)


class TestLoadConfig(unittest.TestCase):
    """Configuration loading tests"""

    def setUp(self):
        """Test setup"""
        # Clear environment variables
        self.original_env = os.environ.copy()
        # Ensure clearing environment variables that might affect tests
        os.environ.pop("FORCE_UPDATE", None)

    def tearDown(self):
        """Test cleanup"""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_load_config_cdn(self):
        """Test loading CDN configuration"""
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "CLOUD_ACCESS_KEY_ID": "test_key_id",
                "CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "CDN_DOMAIN_NAME": "test.example.com",
                "CDN_CERT": "test_cert",
                "CDN_CERT_PRIVATE_KEY": "test_key",
                "CDN_REGION": "cn-hangzhou",
                "FORCE_UPDATE": "false",  # Explicitly set to false
            }
        )

        result = load_config()
        self.assertIsInstance(result, AppConfig)
        self.assertEqual(result.service_type, "cdn")
        self.assertEqual(result.credentials.access_key_id, "test_key_id")
        self.assertEqual(result.credentials.access_key_secret, "test_key_secret")
        self.assertIsNotNone(result.cdn_config)
        self.assertEqual(result.cdn_config.domain_name, "test.example.com")
        self.assertEqual(result.cdn_config.cert, "test_cert")
        self.assertEqual(result.cdn_config.cert_private_key, "test_key")
        self.assertEqual(result.cdn_config.region, "cn-hangzhou")
        self.assertEqual(result.force_update, False)  # force defaults to False

    def test_load_config_lb(self):
        """Test loading Load Balancer configuration (formerly SLB)"""
        os.environ.update(
            {
                "SERVICE_TYPE": "lb",
                "CLOUD_ACCESS_KEY_ID": "test_key_id",
                "CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "LB_INSTANCE_ID": "test-instance-id",
                "LB_LISTENER_PORT": "443",
                "LB_CERT": "test_cert",
                "LB_CERT_PRIVATE_KEY": "test_key",
                "LB_REGION": "cn-beijing",
                "FORCE_UPDATE": "false",  # Explicitly set to false
            }
        )

        result = load_config()
        self.assertIsInstance(result, AppConfig)
        self.assertEqual(result.service_type, "lb")
        self.assertEqual(result.credentials.access_key_id, "test_key_id")
        self.assertEqual(result.credentials.access_key_secret, "test_key_secret")
        self.assertIsNotNone(result.lb_config)
        self.assertEqual(result.lb_config.instance_id, "test-instance-id")
        self.assertEqual(result.lb_config.listener_port, 443)
        self.assertEqual(result.lb_config.cert, "test_cert")
        self.assertEqual(result.lb_config.cert_private_key, "test_key")
        self.assertEqual(result.lb_config.region, "cn-beijing")
        self.assertEqual(result.force_update, False)  # force defaults to False

    def test_load_config_slb_backward_compat(self):
        """Test backward compatibility: SLB service type automatically converted to lb"""
        os.environ.update(
            {
                "SERVICE_TYPE": "slb",
                "CLOUD_ACCESS_KEY_ID": "test_key_id",
                "CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "SLB_INSTANCE_ID": "test-instance-id",
                "SLB_LISTENER_PORT": "443",
                "SLB_CERT": "test_cert",
                "SLB_CERT_PRIVATE_KEY": "test_key",
                "SLB_REGION": "cn-beijing",
            }
        )

        result = load_config()
        self.assertEqual(result.service_type, "lb")  # slb automatically converted to lb

    def test_load_config_with_force_update(self):
        """Test loading configuration with force update flag"""
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "CLOUD_ACCESS_KEY_ID": "test_key_id",
                "CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "CDN_DOMAIN_NAME": "test.example.com",
                "CDN_CERT": "test_cert",
                "CDN_CERT_PRIVATE_KEY": "test_key",
                "CDN_REGION": "cn-hangzhou",
                "FORCE_UPDATE": "true",
            }
        )

        result = load_config()
        self.assertEqual(result.force_update, True)  # force is True

    def test_load_config_with_force_update_false(self):
        """Test force update flag set to false"""
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "CLOUD_ACCESS_KEY_ID": "test_key_id",
                "CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "CDN_DOMAIN_NAME": "test.example.com",
                "CDN_CERT": "test_cert",
                "CDN_CERT_PRIVATE_KEY": "test_key",
                "CDN_REGION": "cn-hangzhou",
                "FORCE_UPDATE": "false",
            }
        )

        result = load_config()
        self.assertEqual(result.force_update, False)  # force is False

    def test_load_config_missing_access_key(self):
        """Test missing access credentials"""
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "CDN_DOMAIN_NAME": "test.example.com",
            }
        )

        with self.assertRaises(ConfigError):
            load_config()

    def test_load_config_missing_domain_name(self):
        """Test missing domain name"""
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "CLOUD_ACCESS_KEY_ID": "test_key_id",
                "CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
            }
        )

        with self.assertRaises(ConfigError):
            load_config()

    def test_load_config_invalid_service_type(self):
        """Test invalid service type"""
        os.environ.update(
            {
                "SERVICE_TYPE": "invalid",
                "CLOUD_ACCESS_KEY_ID": "test_key_id",
                "CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
            }
        )

        with self.assertRaises(ConfigError):
            load_config()

    def test_load_config_with_cloud_provider(self):
        """Test loading configuration with cloud provider"""
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "CLOUD_PROVIDER": "alibaba",
                "CLOUD_ACCESS_KEY_ID": "test_key_id",
                "CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "CDN_DOMAIN_NAME": "test.example.com",
                "CDN_CERT": "test_cert",
                "CDN_CERT_PRIVATE_KEY": "test_key",
                "CDN_REGION": "cn-hangzhou",
            }
        )

        result = load_config()
        self.assertEqual(result.cloud_provider, "alibaba")

    def test_load_config_with_auth_method(self):
        """Test loading configuration with authentication method"""
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "AUTH_METHOD": "access_key",
                "CLOUD_ACCESS_KEY_ID": "test_key_id",
                "CLOUD_ACCESS_KEY_SECRET": "test_key_secret",
                "CDN_DOMAIN_NAME": "test.example.com",
                "CDN_CERT": "test_cert",
                "CDN_CERT_PRIVATE_KEY": "test_key",
                "CDN_REGION": "cn-hangzhou",
            }
        )

        result = load_config()
        self.assertEqual(result.auth_method, "access_key")

    def test_load_config_with_legacy_alibaba_vars(self):
        """Test backward compatibility with legacy ALIBABA_CLOUD_* variables"""
        os.environ.update(
            {
                "SERVICE_TYPE": "cdn",
                "ALIBABA_CLOUD_ACCESS_KEY_ID": "legacy_key_id",
                "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "legacy_key_secret",
                "CDN_DOMAIN_NAME": "test.example.com",
                "CDN_CERT": "test_cert",
                "CDN_CERT_PRIVATE_KEY": "test_key",
                "CDN_REGION": "cn-hangzhou",
            }
        )

        result = load_config()
        self.assertEqual(result.credentials.access_key_id, "legacy_key_id")
        self.assertEqual(result.credentials.access_key_secret, "legacy_key_secret")


if __name__ == "__main__":
    unittest.main()

