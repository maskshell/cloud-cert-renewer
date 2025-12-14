"""Tests for cloud service clients module

Tests the Alibaba Cloud client implementations
(CdnCertRenewer, LoadBalancerCertRenewer).
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from alibabacloud_cdn20180510.client import Client as Cdn20180510Client
from alibabacloud_slb20140515.client import Client as Slb20140515Client

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.cert_renewer.base import CertValidationError  # noqa: E402
from cloud_cert_renewer.clients.alibaba import (  # noqa: E402
    CdnCertRenewer,
    LoadBalancerCertRenewer,
)


def create_mock_credential_client() -> MagicMock:
    """Create a mock credential client for testing"""
    return MagicMock()


class TestCdnCertRenewer(unittest.TestCase):
    """CDN certificate renewer tests"""

    def setUp(self):
        """Test setup"""
        self.access_key_id = "test_access_key_id"
        self.access_key_secret = "test_access_key_secret"
        self.domain_name = "test.example.com"
        self.credential_client = create_mock_credential_client()
        # Note: These are placeholder certificates (not real certificates).
        # They are safe to use because is_cert_valid() is mocked in all tests
        # that would parse them.
        self.cert = """-----BEGIN CERTIFICATE-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END CERTIFICATE-----"""
        self.cert_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"""
        self.region = "cn-hangzhou"

    def test_create_client(self):
        """Test creating CDN client"""
        client = CdnCertRenewer.create_client(self.credential_client)
        self.assertIsNotNone(client)
        # Verify client type
        self.assertIsInstance(client, Cdn20180510Client)

    @patch("cloud_cert_renewer.clients.alibaba.is_cert_valid")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.create_client")
    def test_renew_cert_success(self, mock_create_client, mock_is_cert_valid):
        """Test successful certificate renewal"""
        # Setup mocks
        mock_is_cert_valid.return_value = True
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
            credential_client=self.credential_client,
        )

        # Verify results
        self.assertTrue(result)
        mock_is_cert_valid.assert_called_once_with(self.cert, self.domain_name)
        mock_client.set_cdn_domain_sslcertificate_with_options.assert_called_once()

    @patch.dict(
        os.environ,
        {
            "CLOUD_API_CONNECT_TIMEOUT": "1000",
            "CLOUD_API_READ_TIMEOUT": "2000",
            "CLOUD_API_MAX_ATTEMPTS": "4",
        },
        clear=True,
    )
    @patch("cloud_cert_renewer.clients.alibaba.util_models.RuntimeOptions")
    @patch("cloud_cert_renewer.clients.alibaba.is_cert_valid")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.create_client")
    def test_runtime_options_from_env(
        self, mock_create_client, mock_is_cert_valid, mock_runtime_cls
    ):
        """RuntimeOptions should reflect timeout/retry env vars."""
        mock_is_cert_valid.return_value = True

        runtime = MagicMock()
        mock_runtime_cls.return_value = runtime

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.set_cdn_domain_sslcertificate_with_options.return_value = (
            mock_response
        )
        mock_create_client.return_value = mock_client

        result = CdnCertRenewer.renew_cert(
            domain_name=self.domain_name,
            cert=self.cert,
            cert_private_key=self.cert_private_key,
            region=self.region,
            credential_client=self.credential_client,
        )

        self.assertTrue(result)
        self.assertEqual(runtime.connect_timeout, 1000)
        self.assertEqual(runtime.read_timeout, 2000)
        self.assertTrue(runtime.autoretry)
        self.assertEqual(runtime.max_attempts, 4)

        args, _ = mock_client.set_cdn_domain_sslcertificate_with_options.call_args
        self.assertIs(args[1], runtime)

    @patch("cloud_cert_renewer.clients.alibaba.is_cert_valid")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.get_current_cert")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.create_client")
    def test_renew_cert_does_not_query_current_cert(
        self, mock_create_client, mock_get_current_cert, mock_is_cert_valid
    ):
        """Test client update does not query current cert for fingerprint comparison"""
        mock_is_cert_valid.return_value = True
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.set_cdn_domain_sslcertificate_with_options.return_value = (
            mock_response
        )
        mock_create_client.return_value = mock_client

        result = CdnCertRenewer.renew_cert(
            domain_name=self.domain_name,
            cert=self.cert,
            cert_private_key=self.cert_private_key,
            region=self.region,
            credential_client=self.credential_client,
        )

        self.assertTrue(result)
        mock_get_current_cert.assert_not_called()
        mock_client.set_cdn_domain_sslcertificate_with_options.assert_called_once()

    @patch("cloud_cert_renewer.clients.alibaba.is_cert_valid")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.create_client")
    def test_renew_cert_force_update(self, mock_create_client, mock_is_cert_valid):
        """Test force flag still performs the update"""
        # Setup mocks
        mock_is_cert_valid.return_value = True
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
            credential_client=self.credential_client,
            force=True,
        )

        # Verify results
        self.assertTrue(result)
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
                credential_client=self.credential_client,
            )


class TestLoadBalancerCertRenewer(unittest.TestCase):
    """Load Balancer certificate renewer tests (formerly SLB)"""

    def setUp(self):
        """Test setup"""
        self.access_key_id = "test_access_key_id"
        self.access_key_secret = "test_access_key_secret"
        self.instance_id = "test-instance-id"
        self.listener_port = 443
        self.region = "cn-hangzhou"
        self.credential_client = create_mock_credential_client()
        # Note: These are placeholder certificates (not real certificates).
        # They are safe to use because certificate validation is mocked in tests.
        self.cert = """-----BEGIN CERTIFICATE-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END CERTIFICATE-----"""
        self.cert_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"""

    def test_create_client(self):
        """Test creating SLB client"""
        client = LoadBalancerCertRenewer.create_client(self.credential_client)
        self.assertIsNotNone(client)
        # Verify client type
        self.assertIsInstance(client, Slb20140515Client)

    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_renew_cert_success(self, mock_create_client):
        """Test successful certificate renewal"""
        # Setup mocks
        mock_client = MagicMock()
        mock_upload_response = MagicMock()
        mock_upload_response.body = MagicMock()
        mock_upload_response.body.server_certificate_id = "test-cert-id"
        mock_client.upload_server_certificate_with_options.return_value = (
            mock_upload_response
        )
        mock_bind_response = MagicMock()
        mock_bind_response.status_code = 200
        mock_client.set_load_balancer_https_listener_attribute_with_options.return_value = (  # noqa: E501
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
            credential_client=self.credential_client,
        )

        # Verify results
        self.assertTrue(result)
        mock_client.upload_server_certificate_with_options.assert_called_once()
        mock_client.set_load_balancer_https_listener_attribute_with_options.assert_called_once()

    @patch.dict(
        os.environ,
        {
            "CLOUD_API_CONNECT_TIMEOUT": "1500",
            "CLOUD_API_READ_TIMEOUT": "2500",
        },
        clear=True,
    )
    @patch("cloud_cert_renewer.clients.alibaba.util_models.RuntimeOptions")
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_runtime_options_from_env(self, mock_create_client, mock_runtime_cls):
        """LB client calls should pass RuntimeOptions with env-configured timeouts."""
        runtime = MagicMock()
        mock_runtime_cls.return_value = runtime

        mock_client = MagicMock()
        mock_upload_response = MagicMock()
        mock_upload_response.body = MagicMock()
        mock_upload_response.body.server_certificate_id = "test-cert-id"
        mock_client.upload_server_certificate_with_options.return_value = (
            mock_upload_response
        )
        mock_bind_response = MagicMock()
        mock_bind_response.status_code = 200
        mock_client.set_load_balancer_https_listener_attribute_with_options.return_value = (  # noqa: E501
            mock_bind_response
        )
        mock_create_client.return_value = mock_client

        result = LoadBalancerCertRenewer.renew_cert(
            instance_id=self.instance_id,
            listener_port=self.listener_port,
            cert=self.cert,
            cert_private_key=self.cert_private_key,
            region=self.region,
            credential_client=self.credential_client,
        )

        self.assertTrue(result)
        self.assertEqual(runtime.connect_timeout, 1500)
        self.assertEqual(runtime.read_timeout, 2500)

        upload_args, _ = mock_client.upload_server_certificate_with_options.call_args
        self.assertIs(upload_args[1], runtime)

    @patch(
        "cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.get_current_cert_fingerprint"
    )
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_renew_cert_does_not_query_current_fingerprint(
        self, mock_create_client, mock_get_current_cert_fingerprint
    ):
        """Test client update does not query current fingerprint for comparison"""
        mock_client = MagicMock()
        mock_upload_response = MagicMock()
        mock_upload_response.body = MagicMock()
        mock_upload_response.body.server_certificate_id = "test-cert-id"
        mock_client.upload_server_certificate_with_options.return_value = (
            mock_upload_response
        )
        mock_bind_response = MagicMock()
        mock_bind_response.status_code = 200
        mock_client.set_load_balancer_https_listener_attribute_with_options.return_value = (  # noqa: E501
            mock_bind_response
        )
        mock_create_client.return_value = mock_client

        result = LoadBalancerCertRenewer.renew_cert(
            instance_id=self.instance_id,
            listener_port=self.listener_port,
            cert=self.cert,
            cert_private_key=self.cert_private_key,
            region=self.region,
            credential_client=self.credential_client,
        )

        self.assertTrue(result)
        mock_get_current_cert_fingerprint.assert_not_called()

    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_renew_cert_force_update(self, mock_create_client):
        """Test force flag still performs the update"""
        # Setup mocks
        mock_client = MagicMock()
        mock_upload_response = MagicMock()
        mock_upload_response.body = MagicMock()
        mock_upload_response.body.server_certificate_id = "test-cert-id"
        mock_client.upload_server_certificate_with_options.return_value = (
            mock_upload_response
        )
        mock_bind_response = MagicMock()
        mock_bind_response.status_code = 200
        mock_client.set_load_balancer_https_listener_attribute_with_options.return_value = (  # noqa: E501
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
            credential_client=self.credential_client,
            force=True,
        )

        # Verify results
        self.assertTrue(result)
        mock_client.upload_server_certificate_with_options.assert_called_once()
        mock_client.set_load_balancer_https_listener_attribute_with_options.assert_called_once()


class TestCdnCertRenewerErrorHandling(unittest.TestCase):
    """CDN certificate renewer error handling tests"""

    def setUp(self):
        """Test setup"""
        self.access_key_id = "test_access_key_id"
        self.access_key_secret = "test_access_key_secret"
        self.domain_name = "test.example.com"
        self.credential_client = create_mock_credential_client()
        # Note: These are placeholder certificates (not real certificates).
        # They are safe to use because is_cert_valid() is mocked in all tests
        # that would parse them.
        self.cert = """-----BEGIN CERTIFICATE-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END CERTIFICATE-----"""
        self.cert_private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpQIBAAKCAQEA...
-----END RSA PRIVATE KEY-----"""
        self.region = "cn-hangzhou"

    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.create_client")
    def test_get_current_cert_exception_handling(self, mock_create_client):
        """Test get_current_cert handles exceptions gracefully"""
        mock_client = MagicMock()
        mock_client.describe_domain_certificate_info_with_options.side_effect = (
            Exception("API Error")
        )
        mock_create_client.return_value = mock_client

        result = CdnCertRenewer.get_current_cert(
            domain_name=self.domain_name,
            credential_client=self.credential_client,
        )

        self.assertIsNone(result)

    @patch("cloud_cert_renewer.clients.alibaba.is_cert_valid")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.get_current_cert")
    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.create_client")
    def test_renew_cert_exception_handling(
        self, mock_create_client, mock_get_current_cert, mock_is_cert_valid
    ):
        """Test renew_cert handles exceptions and logs diagnostic URL"""
        mock_is_cert_valid.return_value = True
        mock_get_current_cert.return_value = None
        mock_client = MagicMock()
        mock_error = Exception("API Error")
        mock_error.message = "Error message"
        mock_error.data = {"Recommend": "https://diagnostic.url"}
        mock_client.set_cdn_domain_sslcertificate_with_options.side_effect = mock_error
        mock_create_client.return_value = mock_client

        with self.assertRaises(Exception):
            CdnCertRenewer.renew_cert(
                domain_name=self.domain_name,
                cert=self.cert,
                cert_private_key=self.cert_private_key,
                region=self.region,
                credential_client=self.credential_client,
            )


class TestLoadBalancerCertRenewerErrorHandling(unittest.TestCase):
    """Load Balancer certificate renewer error handling tests"""

    def setUp(self):
        """Test setup"""
        self.access_key_id = "test_access_key_id"
        self.access_key_secret = "test_access_key_secret"
        self.instance_id = "test-instance-id"
        self.listener_port = 443
        self.region = "cn-hangzhou"
        self.credential_client = create_mock_credential_client()

    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_get_listener_cert_id_exception_handling(self, mock_create_client):
        """Test get_listener_cert_id handles exceptions gracefully"""
        mock_client = MagicMock()
        mock_client.describe_load_balancer_https_listener_attribute_with_options.side_effect = (  # noqa: E501
            Exception("API Error")
        )
        mock_create_client.return_value = mock_client

        result = LoadBalancerCertRenewer.get_listener_cert_id(
            instance_id=self.instance_id,
            listener_port=self.listener_port,
            region=self.region,
            credential_client=self.credential_client,
        )

        self.assertIsNone(result)

    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_get_current_cert_fingerprint_exception_handling(self, mock_create_client):
        """Test get_current_cert_fingerprint handles exceptions gracefully"""
        mock_client = MagicMock()
        mock_client.describe_server_certificates_with_options.side_effect = Exception(
            "API Error"
        )
        mock_create_client.return_value = mock_client

        with patch(
            "cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.get_listener_cert_id"
        ) as mock_get_cert_id:
            mock_get_cert_id.return_value = "test-cert-id"

            result = LoadBalancerCertRenewer.get_current_cert_fingerprint(
                instance_id=self.instance_id,
                listener_port=self.listener_port,
                region=self.region,
                credential_client=self.credential_client,
            )

            self.assertIsNone(result)

    @patch(
        "cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.get_current_cert_fingerprint"
    )
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_renew_cert_exception_handling(
        self, mock_create_client, mock_get_current_cert_fingerprint
    ):
        """Test renew_cert handles exceptions and logs diagnostic URL"""
        mock_get_current_cert_fingerprint.return_value = None
        mock_client = MagicMock()
        mock_error = Exception("API Error")
        mock_error.message = "Error message"
        mock_error.data = {"Recommend": "https://diagnostic.url"}
        mock_client.upload_server_certificate_with_options.side_effect = mock_error
        mock_create_client.return_value = mock_client

        with self.assertRaises(Exception):
            LoadBalancerCertRenewer.renew_cert(
                instance_id=self.instance_id,
                listener_port=self.listener_port,
                cert="test_cert",
                cert_private_key="test_key",
                region=self.region,
                credential_client=self.credential_client,
            )

    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.create_client")
    def test_get_current_cert_with_response_body(self, mock_create_client):
        """Test get_current_cert with valid response body"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.body = MagicMock()
        mock_response.body.cert_infos = MagicMock()
        mock_response.body.cert_infos.cert_info = [MagicMock()]
        mock_response.body.cert_infos.cert_info[
            0
        ].server_certificate = "test_cert_content"
        mock_client.describe_domain_certificate_info_with_options.return_value = (
            mock_response
        )
        mock_create_client.return_value = mock_client

        result = CdnCertRenewer.get_current_cert(
            domain_name="test.example.com",
            credential_client=create_mock_credential_client(),
        )

        self.assertEqual(result, "test_cert_content")

    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.create_client")
    def test_get_current_cert_no_cert_info(self, mock_create_client):
        """Test get_current_cert when response has no cert_info"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.body = MagicMock()
        mock_response.body.cert_infos = None
        mock_client.describe_domain_certificate_info_with_options.return_value = (
            mock_response
        )
        mock_create_client.return_value = mock_client

        result = CdnCertRenewer.get_current_cert(
            domain_name="test.example.com",
            credential_client=create_mock_credential_client(),
        )

        self.assertIsNone(result)

    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_get_listener_cert_id_with_response(self, mock_create_client):
        """Test get_listener_cert_id with valid response"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.body = MagicMock()
        mock_response.body.server_certificate_id = "test-cert-id"
        mock_client.describe_load_balancer_https_listener_attribute_with_options.return_value = (  # noqa: E501
            mock_response
        )
        mock_create_client.return_value = mock_client

        result = LoadBalancerCertRenewer.get_listener_cert_id(
            instance_id="test-instance-id",
            listener_port=443,
            region="cn-hangzhou",
            credential_client=create_mock_credential_client(),
        )

        self.assertEqual(result, "test-cert-id")

    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_get_listener_cert_id_no_cert_id(self, mock_create_client):
        """Test get_listener_cert_id when response has no server_certificate_id"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.body = MagicMock()
        mock_response.body.server_certificate_id = None
        mock_client.describe_load_balancer_https_listener_attribute_with_options.return_value = (  # noqa: E501
            mock_response
        )
        mock_create_client.return_value = mock_client

        result = LoadBalancerCertRenewer.get_listener_cert_id(
            instance_id="test-instance-id",
            listener_port=443,
            region="cn-hangzhou",
            credential_client=create_mock_credential_client(),
        )

        self.assertIsNone(result)

    @patch(
        "cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.get_listener_cert_id"
    )
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_get_current_cert_fingerprint_no_cert_id(
        self, mock_create_client, mock_get_cert_id
    ):
        """Test get_current_cert_fingerprint when cert_id is None"""
        mock_get_cert_id.return_value = None

        result = LoadBalancerCertRenewer.get_current_cert_fingerprint(
            instance_id="test-instance-id",
            listener_port=443,
            region="cn-hangzhou",
            credential_client=create_mock_credential_client(),
        )

        self.assertIsNone(result)

    @patch(
        "cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.get_listener_cert_id"
    )
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_get_current_cert_fingerprint_with_response(
        self, mock_create_client, mock_get_cert_id
    ):
        """Test get_current_cert_fingerprint with valid response"""
        mock_get_cert_id.return_value = "test-cert-id"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.body = MagicMock()
        mock_response.body.server_certificates = MagicMock()
        mock_cert = MagicMock()
        mock_cert.fingerprint = "test:fingerprint:value"
        mock_response.body.server_certificates.server_certificate = [mock_cert]
        mock_client.describe_server_certificates_with_options.return_value = (
            mock_response
        )
        mock_create_client.return_value = mock_client

        result = LoadBalancerCertRenewer.get_current_cert_fingerprint(
            instance_id="test-instance-id",
            listener_port=443,
            region="cn-hangzhou",
            credential_client=create_mock_credential_client(),
        )

        self.assertEqual(result, "test:fingerprint:value")

    @patch(
        "cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.get_listener_cert_id"
    )
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_get_current_cert_fingerprint_no_certs(
        self, mock_create_client, mock_get_cert_id
    ):
        """Test get_current_cert_fingerprint when response has no certificates"""
        mock_get_cert_id.return_value = "test-cert-id"
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.body = MagicMock()
        mock_response.body.server_certificates = None
        mock_client.describe_server_certificates_with_options.return_value = (
            mock_response
        )
        mock_create_client.return_value = mock_client

        result = LoadBalancerCertRenewer.get_current_cert_fingerprint(
            instance_id="test-instance-id",
            listener_port=443,
            region="cn-hangzhou",
            credential_client=create_mock_credential_client(),
        )

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
