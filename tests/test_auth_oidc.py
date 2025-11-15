"""Tests for OIDC credential provider

Tests the OIDC credential provider implementation for RRSA authentication.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.auth.factory import CredentialProviderFactory  # noqa: E402
from cloud_cert_renewer.auth.oidc import OidcCredentialProvider  # noqa: E402


class TestOidcCredentialProvider(unittest.TestCase):
    """OIDC credential provider tests"""

    def setUp(self):
        """Test setup"""
        self.role_arn = "acs:ram::123456789012:role/test-role"
        self.oidc_provider_arn = "acs:ram::123456789012:oidc-provider/test-provider"
        self.oidc_token_file = "/tmp/oidc-token"

    def test_init_with_parameters(self):
        """Test OidcCredentialProvider initialization with parameters"""
        provider = OidcCredentialProvider(
            role_arn=self.role_arn,
            oidc_provider_arn=self.oidc_provider_arn,
            oidc_token_file_path=self.oidc_token_file,
            role_session_name="test-session",
        )

        self.assertEqual(provider.role_arn, self.role_arn)
        self.assertEqual(provider.oidc_provider_arn, self.oidc_provider_arn)
        self.assertEqual(provider.oidc_token_file_path, self.oidc_token_file)
        self.assertEqual(provider.role_session_name, "test-session")

    def test_init_with_defaults(self):
        """Test OidcCredentialProvider initialization with defaults"""
        provider = OidcCredentialProvider()

        self.assertIsNone(provider.role_arn)
        self.assertIsNone(provider.oidc_provider_arn)
        self.assertIsNone(provider.oidc_token_file_path)
        self.assertEqual(provider.role_session_name, "cert-renewer-oidc-session")

    @patch.dict(
        os.environ,
        {
            "ALIBABA_CLOUD_ROLE_ARN": "acs:ram::123456789012:role/test-role",
            "ALIBABA_CLOUD_OIDC_PROVIDER_ARN": (
                "acs:ram::123456789012:oidc-provider/test-provider"
            ),
        },
    )
    @patch("cloud_cert_renewer.auth.oidc.CredClient")
    def test_get_credential_client_from_env(self, mock_cred_client_class):
        """Test getting credential client from environment variables"""
        mock_cred_client = MagicMock()
        mock_cred_client_class.return_value = mock_cred_client

        provider = OidcCredentialProvider()
        provider.get_credential_client()

        # Verify CredClient was created with correct config
        mock_cred_client_class.assert_called_once()
        call_args = mock_cred_client_class.call_args
        config = call_args[0][0]

        self.assertEqual(config.type, "oidc_role_arn")
        self.assertEqual(config.role_arn, "acs:ram::123456789012:role/test-role")
        self.assertEqual(
            config.oidc_provider_arn,
            "acs:ram::123456789012:oidc-provider/test-provider",
        )
        self.assertEqual(config.role_session_name, "cert-renewer-oidc-session")

    @patch("cloud_cert_renewer.auth.oidc.CredClient")
    def test_get_credential_client_with_parameters(self, mock_cred_client_class):
        """Test getting credential client with explicit parameters"""
        mock_cred_client = MagicMock()
        mock_cred_client_class.return_value = mock_cred_client

        provider = OidcCredentialProvider(
            role_arn=self.role_arn,
            oidc_provider_arn=self.oidc_provider_arn,
            oidc_token_file_path=self.oidc_token_file,
        )
        provider.get_credential_client()

        # Verify CredClient was created with correct config
        mock_cred_client_class.assert_called_once()
        call_args = mock_cred_client_class.call_args
        config = call_args[0][0]

        self.assertEqual(config.type, "oidc_role_arn")
        self.assertEqual(config.role_arn, self.role_arn)
        self.assertEqual(config.oidc_provider_arn, self.oidc_provider_arn)
        self.assertEqual(config.oidc_token_file_path, self.oidc_token_file)

    @patch.dict(os.environ, {})
    def test_get_credential_client_missing_role_arn(self):
        """Test error when role_arn is missing"""
        provider = OidcCredentialProvider()

        with self.assertRaises(ValueError) as context:
            provider.get_credential_client()

        self.assertIn("role_arn", str(context.exception))
        self.assertIn("ALIBABA_CLOUD_ROLE_ARN", str(context.exception))

    @patch.dict(
        os.environ,
        {
            "ALIBABA_CLOUD_ROLE_ARN": "acs:ram::123456789012:role/test-role",
        },
    )
    def test_get_credential_client_missing_oidc_provider_arn(self):
        """Test error when oidc_provider_arn is missing"""
        provider = OidcCredentialProvider()

        with self.assertRaises(ValueError) as context:
            provider.get_credential_client()

        self.assertIn("oidc_provider_arn", str(context.exception))
        self.assertIn("ALIBABA_CLOUD_OIDC_PROVIDER_ARN", str(context.exception))

    @patch.dict(
        os.environ,
        {
            "ALIBABA_CLOUD_ROLE_ARN": "acs:ram::123456789012:role/test-role",
            "ALIBABA_CLOUD_OIDC_PROVIDER_ARN": (
                "acs:ram::123456789012:oidc-provider/test-provider"
            ),
        },
    )
    @patch("cloud_cert_renewer.auth.oidc.CredClient")
    def test_get_credentials(self, mock_cred_client_class):
        """Test getting credentials from OIDC"""
        mock_credential = MagicMock()
        mock_credential.access_key_id = "test_access_key_id"
        mock_credential.access_key_secret = "test_access_key_secret"
        mock_credential.security_token = "test_security_token"

        mock_cred_client = MagicMock()
        mock_cred_client.get_credential.return_value = mock_credential
        mock_cred_client_class.return_value = mock_cred_client

        provider = OidcCredentialProvider()
        credentials = provider.get_credentials()

        self.assertEqual(credentials.access_key_id, "test_access_key_id")
        self.assertEqual(credentials.access_key_secret, "test_access_key_secret")
        self.assertEqual(credentials.security_token, "test_security_token")
        mock_cred_client.get_credential.assert_called_once()

    def test_factory_create_oidc(self):
        """Test CredentialProviderFactory creating OidcCredentialProvider"""
        provider = CredentialProviderFactory.create(auth_method="oidc")

        self.assertIsInstance(provider, OidcCredentialProvider)

    @patch.dict(
        os.environ,
        {
            "ALIBABA_CLOUD_ROLE_ARN": "acs:ram::123456789012:role/test-role",
            "ALIBABA_CLOUD_OIDC_PROVIDER_ARN": (
                "acs:ram::123456789012:oidc-provider/test-provider"
            ),
            "ALIBABA_CLOUD_OIDC_TOKEN_FILE": "/tmp/oidc-token",
        },
    )
    def test_factory_create_oidc_with_kwargs(self):
        """Test CredentialProviderFactory creating OidcCredentialProvider with kwargs"""
        provider = CredentialProviderFactory.create(
            auth_method="oidc",
            role_arn="custom-role-arn",
            role_session_name="custom-session",
        )

        self.assertIsInstance(provider, OidcCredentialProvider)
        self.assertEqual(provider.role_arn, "custom-role-arn")
        self.assertEqual(provider.role_session_name, "custom-session")
