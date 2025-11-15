"""Tests for cloud service provider adapters (Adapter Pattern)

Tests the Adapter Pattern implementation for cloud service providers.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.config.models import Credentials  # noqa: E402
from cloud_cert_renewer.providers.alibaba import AlibabaCloudAdapter  # noqa: E402
from cloud_cert_renewer.providers.base import (  # noqa: E402
    CloudAdapter,
    CloudAdapterFactory,
)


class TestAlibabaCloudAdapter(unittest.TestCase):
    """Alibaba Cloud adapter tests (Adapter Pattern)"""

    def setUp(self):
        """Test setup"""
        self.adapter = AlibabaCloudAdapter()
        self.credentials = Credentials(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
        )

    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.renew_cert")
    @patch("cloud_cert_renewer.providers.alibaba.CredentialProviderFactory")
    def test_update_cdn_certificate(self, mock_factory, mock_renew_cert):
        """Test updating CDN certificate through adapter"""
        mock_renew_cert.return_value = True
        mock_provider = MagicMock()
        mock_credential_client = MagicMock()
        mock_provider.get_credential_client.return_value = mock_credential_client
        mock_factory.create.return_value = mock_provider

        result = self.adapter.update_cdn_certificate(
            domain_name="test.example.com",
            cert="test_cert",
            cert_private_key="test_key",
            region="cn-hangzhou",
            credentials=self.credentials,
        )

        self.assertTrue(result)
        mock_renew_cert.assert_called_once_with(
            domain_name="test.example.com",
            cert="test_cert",
            cert_private_key="test_key",
            region="cn-hangzhou",
            credential_client=mock_credential_client,
            force=False,
        )

    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.renew_cert")
    @patch("cloud_cert_renewer.providers.alibaba.CredentialProviderFactory")
    def test_update_load_balancer_certificate(self, mock_factory, mock_renew_cert):
        """Test updating Load Balancer certificate through adapter"""
        mock_renew_cert.return_value = True
        mock_provider = MagicMock()
        mock_credential_client = MagicMock()
        mock_provider.get_credential_client.return_value = mock_credential_client
        mock_factory.create.return_value = mock_provider

        result = self.adapter.update_load_balancer_certificate(
            instance_id="test-instance-id",
            listener_port=443,
            cert="test_cert",
            cert_private_key="test_key",
            region="cn-hangzhou",
            credentials=self.credentials,
        )

        self.assertTrue(result)
        mock_renew_cert.assert_called_once_with(
            instance_id="test-instance-id",
            listener_port=443,
            cert="test_cert",
            cert_private_key="test_key",
            region="cn-hangzhou",
            credential_client=mock_credential_client,
            force=False,
        )

    @patch("cloud_cert_renewer.clients.alibaba.CdnCertRenewer.get_current_cert")
    @patch("cloud_cert_renewer.providers.alibaba.CredentialProviderFactory")
    def test_get_current_cdn_certificate(self, mock_factory, mock_get_cert):
        """Test getting current CDN certificate through adapter"""
        mock_get_cert.return_value = "current_cert_content"
        mock_provider = MagicMock()
        mock_credential_client = MagicMock()
        mock_provider.get_credential_client.return_value = mock_credential_client
        mock_factory.create.return_value = mock_provider

        result = self.adapter.get_current_cdn_certificate(
            domain_name="test.example.com",
            region="cn-hangzhou",
            credentials=self.credentials,
        )

        self.assertEqual(result, "current_cert_content")
        mock_get_cert.assert_called_once_with(
            domain_name="test.example.com",
            credential_client=mock_credential_client,
        )

    @patch(
        "cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.get_current_cert_fingerprint"
    )
    @patch("cloud_cert_renewer.providers.alibaba.CredentialProviderFactory")
    def test_get_current_lb_certificate_fingerprint(
        self, mock_factory, mock_get_fingerprint
    ):
        """Test getting current LB certificate fingerprint through adapter"""
        mock_get_fingerprint.return_value = "test:fingerprint"
        mock_provider = MagicMock()
        mock_credential_client = MagicMock()
        mock_provider.get_credential_client.return_value = mock_credential_client
        mock_factory.create.return_value = mock_provider

        result = self.adapter.get_current_lb_certificate_fingerprint(
            instance_id="test-instance-id",
            listener_port=443,
            region="cn-hangzhou",
            credentials=self.credentials,
        )

        self.assertEqual(result, "test:fingerprint")
        mock_get_fingerprint.assert_called_once_with(
            instance_id="test-instance-id",
            listener_port=443,
            region="cn-hangzhou",
            credential_client=mock_credential_client,
        )

    def test_adapter_implements_interface(self):
        """Test that adapter implements CloudAdapter interface"""
        self.assertIsInstance(self.adapter, CloudAdapter)


class TestCloudAdapterFactory(unittest.TestCase):
    """Cloud adapter factory tests (Factory Pattern)"""

    def test_factory_create_alibaba_adapter(self):
        """Test factory creates Alibaba Cloud adapter"""
        adapter = CloudAdapterFactory.create("alibaba")

        self.assertIsInstance(adapter, CloudAdapter)
        self.assertIsInstance(adapter, AlibabaCloudAdapter)

    def test_factory_invalid_provider(self):
        """Test factory raises error for invalid cloud provider"""
        with self.assertRaises(ValueError) as context:
            CloudAdapterFactory.create("invalid")

        self.assertIn("Unsupported cloud service provider", str(context.exception))

    def test_factory_case_insensitive(self):
        """Test factory is case insensitive for cloud provider"""
        adapter1 = CloudAdapterFactory.create("ALIBABA")
        adapter2 = CloudAdapterFactory.create("alibaba")

        self.assertIsInstance(adapter1, AlibabaCloudAdapter)
        self.assertIsInstance(adapter2, AlibabaCloudAdapter)


if __name__ == "__main__":
    unittest.main()
