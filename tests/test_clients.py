"""Tests for cloud service clients module

Tests the Alibaba Cloud client implementations (CdnCertRenewer, LoadBalancerCertRenewer).
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from alibabacloud_cdn20180510.client import Client as Cdn20180510Client
from alibabacloud_slb20140515.client import Client as Slb20140515Client

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.cert_renewer.base import CertValidationError
from cloud_cert_renewer.clients.alibaba import (
    CdnCertRenewer,
    LoadBalancerCertRenewer,
)


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


if __name__ == "__main__":
    unittest.main()

