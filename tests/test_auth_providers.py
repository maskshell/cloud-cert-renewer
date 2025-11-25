"""Tests for credential providers (Strategy Pattern)

Tests the various credential provider implementations (Strategy Pattern).
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cloud_cert_renewer.auth.access_key import AccessKeyCredentialProvider  # noqa: E402
from cloud_cert_renewer.auth.env import EnvCredentialProvider  # noqa: E402
from cloud_cert_renewer.auth.service_account import (  # noqa: E402
    ServiceAccountCredentialProvider,
)
from cloud_cert_renewer.auth.sts import STSCredentialProvider  # noqa: E402
from cloud_cert_renewer.config.models import Credentials  # noqa: E402


class TestAccessKeyCredentialProvider(unittest.TestCase):
    """AccessKey credential provider tests"""

    def setUp(self):
        """Test setup"""
        self.provider = AccessKeyCredentialProvider(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
        )

    def test_get_credentials(self):
        """Test getting credentials"""
        credentials = self.provider.get_credentials()

        self.assertIsInstance(credentials, Credentials)
        self.assertEqual(credentials.access_key_id, "test_key_id")
        self.assertEqual(credentials.access_key_secret, "test_key_secret")
        self.assertIsNone(credentials.security_token)


class TestSTSCredentialProvider(unittest.TestCase):
    """STS credential provider tests"""

    def setUp(self):
        """Test setup"""
        self.provider = STSCredentialProvider(
            access_key_id="test_key_id",
            access_key_secret="test_key_secret",
            security_token="test_security_token",
        )

    def test_get_credentials(self):
        """Test getting credentials"""
        credentials = self.provider.get_credentials()

        self.assertIsInstance(credentials, Credentials)
        self.assertEqual(credentials.access_key_id, "test_key_id")
        self.assertEqual(credentials.access_key_secret, "test_key_secret")
        self.assertEqual(credentials.security_token, "test_security_token")


class TestEnvCredentialProvider(unittest.TestCase):
    """Environment variable credential provider tests"""

    def setUp(self):
        """Test setup"""
        self.provider = EnvCredentialProvider()
        self.original_env = os.environ.copy()

    def tearDown(self):
        """Test cleanup"""
        os.environ.clear()
        os.environ.update(self.original_env)

    @patch.dict(
        os.environ,
        {
            "CLOUD_ACCESS_KEY_ID": "env_key_id",
            "CLOUD_ACCESS_KEY_SECRET": "env_key_secret",
        },
    )
    def test_get_credentials_from_env(self):
        """Test getting credentials from environment variables"""
        credentials = self.provider.get_credentials()

        self.assertIsInstance(credentials, Credentials)
        self.assertEqual(credentials.access_key_id, "env_key_id")
        self.assertEqual(credentials.access_key_secret, "env_key_secret")

    @patch.dict(
        os.environ,
        {
            "ALIBABA_CLOUD_ACCESS_KEY_ID": "legacy_key_id",
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "legacy_key_secret",
        },
    )
    def test_get_credentials_from_legacy_env(self):
        """Test getting credentials from legacy environment variables"""
        credentials = self.provider.get_credentials()

        self.assertIsInstance(credentials, Credentials)
        self.assertEqual(credentials.access_key_id, "legacy_key_id")
        self.assertEqual(credentials.access_key_secret, "legacy_key_secret")

    @patch.dict(
        os.environ,
        {
            "CLOUD_ACCESS_KEY_ID": "new_key_id",
            "CLOUD_ACCESS_KEY_SECRET": "new_key_secret",
            "ALIBABA_CLOUD_ACCESS_KEY_ID": "legacy_key_id",
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET": "legacy_key_secret",
        },
    )
    def test_get_credentials_prioritizes_new_env(self):
        """Test that new environment variables take priority over legacy ones"""
        credentials = self.provider.get_credentials()

        self.assertEqual(credentials.access_key_id, "new_key_id")
        self.assertEqual(credentials.access_key_secret, "new_key_secret")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_credentials_missing_env(self):
        """Test getting credentials when environment variables are missing"""
        with self.assertRaises(ValueError) as context:
            self.provider.get_credentials()

        self.assertIn("Missing required environment variables", str(context.exception))


class TestServiceAccountCredentialProvider(unittest.TestCase):
    """ServiceAccount credential provider tests"""

    def setUp(self):
        """Test setup"""
        self.role_arn = "acs:ram::123456789012:role/test-role"
        self.oidc_provider_arn = "acs:ram::123456789012:oidc-provider/test-provider"
        self.token_content = "fake-jwt-token-for-testing"

    def tearDown(self):
        """Test cleanup"""
        # Clean up any environment variables
        for key in ["ALIBABA_CLOUD_ROLE_ARN", "CLOUD_ROLE_ARN"]:
            if key in os.environ:
                del os.environ[key]

    def test_init_with_defaults(self):
        """Test ServiceAccountCredentialProvider initialization with defaults"""
        provider = ServiceAccountCredentialProvider()

        self.assertEqual(
            provider.service_account_path,
            "/var/run/secrets/kubernetes.io/serviceaccount",
        )
        self.assertIsNone(provider.role_arn)
        self.assertIsNone(provider.oidc_provider_arn)
        self.assertEqual(
            provider.role_session_name, "cert-renewer-service-account-session"
        )

    def test_init_with_parameters(self):
        """Test ServiceAccountCredentialProvider initialization with parameters"""
        provider = ServiceAccountCredentialProvider(
            service_account_path="/custom/path",
            role_arn=self.role_arn,
            oidc_provider_arn=self.oidc_provider_arn,
            role_session_name="custom-session",
        )

        self.assertEqual(provider.service_account_path, "/custom/path")
        self.assertEqual(provider.role_arn, self.role_arn)
        self.assertEqual(provider.oidc_provider_arn, self.oidc_provider_arn)
        self.assertEqual(provider.role_session_name, "custom-session")

    @patch.dict(
        os.environ,
        {
            "ALIBABA_CLOUD_ROLE_ARN": "acs:ram::123456789012:role/env-role",
            "ALIBABA_CLOUD_OIDC_PROVIDER_ARN": (
                "acs:ram::123456789012:oidc-provider/env-provider"
            ),
        },
    )
    def test_get_role_arn_from_env(self):
        """Test getting role ARN from environment variable"""
        provider = ServiceAccountCredentialProvider()

        role_arn = provider._get_role_arn()

        self.assertEqual(role_arn, "acs:ram::123456789012:role/env-role")

    @patch.dict(
        os.environ,
        {
            "CLOUD_ROLE_ARN": "acs:ram::123456789012:role/alt-role",
            "ALIBABA_CLOUD_OIDC_PROVIDER_ARN": (
                "acs:ram::123456789012:oidc-provider/env-provider"
            ),
        },
    )
    def test_get_role_arn_from_alternative_env(self):
        """Test getting role ARN from alternative environment variable"""
        provider = ServiceAccountCredentialProvider()

        role_arn = provider._get_role_arn()

        self.assertEqual(role_arn, "acs:ram::123456789012:role/alt-role")

    def test_get_role_arn_from_parameter(self):
        """Test getting role ARN from parameter takes priority"""
        provider = ServiceAccountCredentialProvider(role_arn=self.role_arn)

        role_arn = provider._get_role_arn()

        self.assertEqual(role_arn, self.role_arn)

    @patch.dict(
        os.environ,
        {
            "ALIBABA_CLOUD_OIDC_PROVIDER_ARN": (
                "acs:ram::123456789012:oidc-provider/env-provider"
            ),
        },
    )
    def test_get_oidc_provider_arn_from_env(self):
        """Test getting OIDC provider ARN from environment variable"""
        provider = ServiceAccountCredentialProvider()

        oidc_provider_arn = provider._get_oidc_provider_arn()

        self.assertEqual(
            oidc_provider_arn, "acs:ram::123456789012:oidc-provider/env-provider"
        )

    def test_get_oidc_provider_arn_from_parameter(self):
        """Test getting OIDC provider ARN from parameter takes priority"""
        provider = ServiceAccountCredentialProvider(
            oidc_provider_arn=self.oidc_provider_arn
        )

        oidc_provider_arn = provider._get_oidc_provider_arn()

        self.assertEqual(oidc_provider_arn, self.oidc_provider_arn)

    def test_get_oidc_token_file_path(self):
        """Test getting OIDC token file path"""
        provider = ServiceAccountCredentialProvider(service_account_path="/custom/path")

        token_path = provider._get_oidc_token_file_path()

        self.assertEqual(token_path, "/custom/path/token")

    def test_get_oidc_token_file_path_default(self):
        """Test getting OIDC token file path with default"""
        provider = ServiceAccountCredentialProvider()

        token_path = provider._get_oidc_token_file_path()

        self.assertEqual(
            token_path,
            "/var/run/secrets/kubernetes.io/serviceaccount/token",
        )

    def test_get_role_arn_missing(self):
        """Test error when role ARN is missing"""
        provider = ServiceAccountCredentialProvider()

        with self.assertRaises(ValueError) as context:
            provider._get_role_arn()

        self.assertIn("role_arn", str(context.exception))
        self.assertIn("ALIBABA_CLOUD_ROLE_ARN", str(context.exception))

    def test_get_oidc_provider_arn_missing(self):
        """Test error when OIDC provider ARN is missing"""
        provider = ServiceAccountCredentialProvider(role_arn=self.role_arn)

        with self.assertRaises(ValueError) as context:
            provider._get_oidc_provider_arn()

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
    @patch("cloud_cert_renewer.auth.service_account.CredClient")
    @patch("cloud_cert_renewer.auth.service_account.os.path.exists")
    def test_get_credential_client(self, mock_exists, mock_cred_client_class):
        """Test getting credential client"""
        mock_exists.return_value = True
        mock_cred_client = MagicMock()
        mock_cred_client_class.return_value = mock_cred_client

        provider = ServiceAccountCredentialProvider()
        client = provider.get_credential_client()

        # Verify CredClient was created
        mock_cred_client_class.assert_called_once()
        self.assertIsNotNone(client)
        # Verify token file check was performed
        mock_exists.assert_called_once()

    @patch("cloud_cert_renewer.auth.service_account.os.path.exists")
    def test_get_credential_client_token_file_not_found(self, mock_exists):
        """Test error when ServiceAccount token file is not found"""
        mock_exists.return_value = False

        provider = ServiceAccountCredentialProvider(
            role_arn=self.role_arn, oidc_provider_arn=self.oidc_provider_arn
        )

        with self.assertRaises(ValueError) as context:
            provider.get_credential_client()

        self.assertIn("ServiceAccount token file not found", str(context.exception))
        mock_exists.assert_called_once()

    @patch.dict(
        os.environ,
        {
            "ALIBABA_CLOUD_ROLE_ARN": "acs:ram::123456789012:role/test-role",
            "ALIBABA_CLOUD_OIDC_PROVIDER_ARN": (
                "acs:ram::123456789012:oidc-provider/test-provider"
            ),
        },
    )
    @patch("cloud_cert_renewer.auth.service_account.CredClient")
    @patch("cloud_cert_renewer.auth.service_account.os.path.exists")
    def test_get_credentials(self, mock_exists, mock_cred_client_class):
        """Test getting credentials from ServiceAccount"""
        mock_exists.return_value = True
        mock_credential = MagicMock()
        mock_credential.access_key_id = "test_access_key_id"
        mock_credential.access_key_secret = "test_access_key_secret"
        mock_credential.security_token = "test_security_token"

        mock_cred_client = MagicMock()
        mock_cred_client.get_credential.return_value = mock_credential
        mock_cred_client_class.return_value = mock_cred_client

        provider = ServiceAccountCredentialProvider()
        credentials = provider.get_credentials()

        self.assertEqual(credentials.access_key_id, "test_access_key_id")
        self.assertEqual(credentials.access_key_secret, "test_access_key_secret")
        self.assertEqual(credentials.security_token, "test_security_token")
        mock_cred_client.get_credential.assert_called_once()
        mock_exists.assert_called_once()


if __name__ == "__main__":
    unittest.main()
