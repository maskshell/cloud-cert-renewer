import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from alibabacloud_cdn20180510.client import Client as Cdn20180510Client
from alibabacloud_slb20140515.client import Client as Slb20140515Client

# Add parent directory to path to import main module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.cert_renewer.base import CertValidationError
from cloud_cert_renewer.clients.alibaba import (
    CdnCertRenewer,
    LoadBalancerCertRenewer,
)
from cloud_cert_renewer.config import ConfigError, load_config
from cloud_cert_renewer.config.models import (
    AppConfig,
    CdnConfig,
    Credentials,
    LoadBalancerConfig,
)

# Backward compatibility: Keep old class names as aliases
CdnCertsRenewer = CdnCertRenewer  # noqa: N816
SlbCertsRenewer = LoadBalancerCertRenewer  # noqa: N816


class TestCdnCertRenewer(unittest.TestCase):
    """CDN certificate renewer tests"""

    def setUp(self):
        """Test setup"""
        self.access_key_id = "test_access_key_id"
        self.access_key_secret = "test_access_key_secret"
        self.domain_name = "test.example.com"
        self.cert = """-----BEGIN CERTIFICATE-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END CERTIFICATE-----"""
        self.cert_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"""
        self.region = "cn-hangzhou"

    def test_create_client(self):
        """Test creating CDN client"""
        client = CdnCertRenewer.create_client(
            self.access_key_id, self.access_key_secret
        )
        self.assertIsNotNone(client)
        # Verify client type
        self.assertIsInstance(client, Cdn20180510Client)

    @patch("cloud_cert_renewer.clients.alibaba.is_cert_valid")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.get_current_cert")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.create_client")
    def test_renew_cert_success(
        self, mock_create_client, mock_get_current_cert, mock_is_cert_valid
    ):
        """Test successful certificate renewal"""
        # Setup mocks
        mock_is_cert_valid.return_value = True
        mock_get_current_cert.return_value = None  # No current certificate, need to update
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.set_cdn_domain_sslcertificate_with_options.return_value = (
            mock_response
        )
        mock_create_client.return_value = mock_client

        # Execute test
        result = CdnCertRenewer.renew_cert(
            domain_name=self.domain_name,
            cert=self.cert,
            cert_private_key=self.cert_private_key,
            region=self.region,
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
        )

        # Verify results
        self.assertTrue(result)
        mock_is_cert_valid.assert_called_once_with(self.cert, self.domain_name)
        mock_get_current_cert.assert_called_once_with(
            self.domain_name, self.access_key_id, self.access_key_secret
        )
        mock_client.set_cdn_domain_sslcertificate_with_options.assert_called_once()

    @patch("cloud_cert_renewer.clients.alibaba.is_cert_valid")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.get_current_cert")
    @patch("cloud_cert_renewer.clients.alibaba.get_cert_fingerprint_sha256")
    def test_renew_cert_skip_when_same(
        self, mock_get_fingerprint, mock_get_current_cert, mock_is_cert_valid
    ):
        """Test skipping renewal when certificate is the same"""
        # Setup mocks
        mock_is_cert_valid.return_value = True
        mock_get_current_cert.return_value = "current_cert_content"
        mock_get_fingerprint.return_value = "SAME:FINGERPRINT:VALUE"

        # Execute test (default force=False)
        result = CdnCertRenewer.renew_cert(
            domain_name=self.domain_name,
            cert=self.cert,
            cert_private_key=self.cert_private_key,
            region=self.region,
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
        )

        # Verify results
        self.assertTrue(result)
        mock_get_current_cert.assert_called_once_with(
            self.domain_name, self.access_key_id, self.access_key_secret
        )
        # Verify fingerprint comparison was called (twice: new cert and current cert)
        self.assertEqual(mock_get_fingerprint.call_count, 2)

    @patch("cloud_cert_renewer.clients.alibaba.is_cert_valid")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.get_current_cert")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.create_client")
    def test_renew_cert_force_update(
        self, mock_create_client, mock_get_current_cert, mock_is_cert_valid
    ):
        """Test force update mode (update even if certificate is the same)"""
        # Setup mocks
        mock_is_cert_valid.return_value = True
        mock_get_current_cert.return_value = "current_cert_content"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.set_cdn_domain_sslcertificate_with_options.return_value = (
            mock_response
        )
        mock_create_client.return_value = mock_client

        # Execute test (force=True)
        result = CdnCertRenewer.renew_cert(
            domain_name=self.domain_name,
            cert=self.cert,
            cert_private_key=self.cert_private_key,
            region=self.region,
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            force=True,
        )

        # Verify results
        self.assertTrue(result)
        # Verify update was executed even with current certificate
        mock_client.set_cdn_domain_sslcertificate_with_options.assert_called_once()

    @patch("cloud_cert_renewer.clients.alibaba.is_cert_valid")
    def test_renew_cert_invalid_cert(self, mock_is_cert_valid):
        """Test certificate validation failure"""
        # Setup mock
        mock_is_cert_valid.return_value = False

        # Execute test and verify exception
        with self.assertRaises(CertValidationError):
            CdnCertRenewer.renew_cert(
                domain_name=self.domain_name,
                cert=self.cert,
                cert_private_key=self.cert_private_key,
                region=self.region,
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
            )


class TestLoadBalancerCertRenewer(unittest.TestCase):
    """Load Balancer certificate renewer tests (formerly SLB)"""

    def setUp(self):
        """Test setup"""
        self.access_key_id = "test_access_key_id"
        self.access_key_secret = "test_access_key_secret"
        self.instance_id = "test-instance-id"
        self.listener_port = 443
        self.cert = """-----BEGIN CERTIFICATE-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END CERTIFICATE-----"""
        self.cert_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"""
        self.region = "cn-hangzhou"

    def test_create_client(self):
        """Test creating SLB client"""
        client = LoadBalancerCertRenewer.create_client(
            self.access_key_id, self.access_key_secret
        )
        self.assertIsNotNone(client)
        # Verify client type
        self.assertIsInstance(client, Slb20140515Client)

    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.get_current_cert_fingerprint")
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_renew_cert_success(
        self, mock_create_client, mock_get_current_cert_fingerprint
    ):
        """Test successful certificate renewal"""
        # Setup mocks
        mock_get_current_cert_fingerprint.return_value = None  # No current certificate, need to update
        mock_client = MagicMock()
        mock_upload_response = MagicMock()
        mock_upload_response.body = MagicMock()
        mock_upload_response.body.server_certificate_id = "test-cert-id"
        mock_client.upload_server_certificate_with_options.return_value = (
            mock_upload_response
        )
        mock_bind_response = MagicMock()
        mock_bind_response.status_code = 200
        mock_client.set_load_balancer_https_listener_attribute_with_options.return_value = (
            mock_bind_response
        )
        mock_create_client.return_value = mock_client

        # Execute test
        result = LoadBalancerCertRenewer.renew_cert(
            instance_id=self.instance_id,
            listener_port=self.listener_port,
            cert=self.cert,
            cert_private_key=self.cert_private_key,
            region=self.region,
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
        )

        # Verify results
        self.assertTrue(result)
        mock_get_current_cert_fingerprint.assert_called_once_with(
            self.instance_id,
            self.listener_port,
            self.region,
            self.access_key_id,
            self.access_key_secret,
        )
        mock_client.upload_server_certificate_with_options.assert_called_once()
        mock_client.set_load_balancer_https_listener_attribute_with_options.assert_called_once()

    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.get_current_cert_fingerprint")
    @patch("cloud_cert_renewer.clients.alibaba.get_cert_fingerprint_sha1")
    def test_renew_cert_skip_when_same(
        self, mock_get_fingerprint, mock_get_current_cert_fingerprint
    ):
        """Test skipping renewal when certificate is the same"""
        # Setup mocks
        mock_get_current_cert_fingerprint.return_value = "same:fingerprint:value"
        mock_get_fingerprint.return_value = "same:fingerprint:value"

        # Execute test (default force=False)
        result = LoadBalancerCertRenewer.renew_cert(
            instance_id=self.instance_id,
            listener_port=self.listener_port,
            cert=self.cert,
            cert_private_key=self.cert_private_key,
            region=self.region,
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
        )

        # Verify results
        self.assertTrue(result)
        mock_get_current_cert_fingerprint.assert_called_once_with(
            self.instance_id,
            self.listener_port,
            self.region,
            self.access_key_id,
            self.access_key_secret,
        )
        # Verify fingerprint comparison was called (once: new cert)
        mock_get_fingerprint.assert_called_once_with(self.cert)

    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.get_current_cert_fingerprint")
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_renew_cert_force_update(
        self, mock_create_client, mock_get_current_cert_fingerprint
    ):
        """Test force update mode (update even if certificate is the same)"""
        # Setup mocks
        mock_get_current_cert_fingerprint.return_value = "same:fingerprint:value"
        mock_client = MagicMock()
        mock_upload_response = MagicMock()
        mock_upload_response.body = MagicMock()
        mock_upload_response.body.server_certificate_id = "test-cert-id"
        mock_client.upload_server_certificate_with_options.return_value = (
            mock_upload_response
        )
        mock_bind_response = MagicMock()
        mock_bind_response.status_code = 200
        mock_client.set_load_balancer_https_listener_attribute_with_options.return_value = (
            mock_bind_response
        )
        mock_create_client.return_value = mock_client

        # Execute test (force=True)
        result = LoadBalancerCertRenewer.renew_cert(
            instance_id=self.instance_id,
            listener_port=self.listener_port,
            cert=self.cert,
            cert_private_key=self.cert_private_key,
            region=self.region,
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            force=True,
        )

        # Verify results
        self.assertTrue(result)
        # Verify update was executed even with same certificate fingerprint
        mock_client.upload_server_certificate_with_options.assert_called_once()
        mock_client.set_load_balancer_https_listener_attribute_with_options.assert_called_once()


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


if __name__ == "__main__":
    unittest.main()
