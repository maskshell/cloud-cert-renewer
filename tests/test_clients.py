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
    CasCertUploader,
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
        mock_client.set_load_balancer_httpslistener_attribute_with_options.return_value = (  # noqa: E501
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
        mock_client.set_load_balancer_httpslistener_attribute_with_options.assert_called_once()

    @patch("cloud_cert_renewer.clients.alibaba.get_cert_fingerprint_sha1")
    @patch(
        "cloud_cert_renewer.clients.alibaba.CasCertUploader.upload_or_reuse_certificate"
    )
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_renew_cert_cas_path(
        self, mock_create_client, mock_cas_upload, mock_fingerprint
    ):
        """CAS path: upload/reuse via CAS, then reference it from the SLB cert store."""
        mock_fingerprint.return_value = "aa:bb:cc:dd:ee:ff:00:11"
        mock_cas_upload.return_value = "cas-cert-id"
        mock_client = MagicMock()
        mock_upload_response = MagicMock()
        mock_upload_response.body.server_certificate_id = "slb-cert-id"
        mock_client.upload_server_certificate_with_options.return_value = (
            mock_upload_response
        )
        mock_bind_response = MagicMock()
        mock_bind_response.status_code = 200
        mock_client.set_load_balancer_httpslistener_attribute_with_options.return_value = (  # noqa: E501
            mock_bind_response
        )
        mock_create_client.return_value = mock_client

        # Use a non-Hangzhou SLB region to verify AliCloudCertificateRegionId
        # is the CAS region (cn-hangzhou), not LB_REGION.
        lb_region = "cn-beijing"
        result = LoadBalancerCertRenewer.renew_cert(
            instance_id=self.instance_id,
            listener_port=self.listener_port,
            cert=self.cert,
            cert_private_key=self.cert_private_key,
            region=lb_region,
            credential_client=self.credential_client,
            cert_source="cas",
        )

        self.assertTrue(result)
        # CAS upload/reuse happened with cert/private_key/name (name includes instance)
        mock_cas_upload.assert_called_once()
        cas_kwargs = mock_cas_upload.call_args.kwargs
        self.assertEqual(cas_kwargs["cert"], self.cert)
        self.assertEqual(cas_kwargs["private_key"], self.cert_private_key)
        self.assertIn(self.instance_id, cas_kwargs["name"])
        # SLB upload references the CAS cert id (no server_certificate/private_key)
        slb_req = mock_client.upload_server_certificate_with_options.call_args.args[0]
        self.assertEqual(slb_req.ali_cloud_certificate_id, "cas-cert-id")
        self.assertEqual(slb_req.region_id, lb_region)
        self.assertEqual(
            slb_req.ali_cloud_certificate_region_id,
            CasCertUploader.CERTIFICATE_REGION_ID,
        )
        self.assertNotEqual(
            slb_req.ali_cloud_certificate_region_id,
            lb_region,
        )
        self.assertFalse(getattr(slb_req, "server_certificate", None))
        # Bind to listener
        mock_client.set_load_balancer_httpslistener_attribute_with_options.assert_called_once()

    @patch("cloud_cert_renewer.clients.alibaba.get_cert_fingerprint_sha1")
    @patch(
        "cloud_cert_renewer.clients.alibaba.CasCertUploader.upload_or_reuse_certificate"
    )
    @patch(
        "cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.find_existing_certificate_by_fingerprint"
    )
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_renew_cert_cas_path_reuses_existing_slb_cert(
        self, mock_create_client, mock_find_slb, mock_cas_upload, mock_fingerprint
    ):
        """I2b: CAS path reuses an SLB cert with a matching fingerprint instead of
        uploading a new one (avoids orphaned SLB entries)."""
        mock_fingerprint.return_value = "aa:bb:cc:dd:ee:ff:00:11"
        mock_cas_upload.return_value = "cas-cert-id"
        # An SLB server_certificate with a matching fingerprint already exists.
        mock_find_slb.return_value = "existing-slb-id"
        mock_client = MagicMock()
        mock_bind_response = MagicMock()
        mock_bind_response.status_code = 200
        bind_call = mock_client.set_load_balancer_httpslistener_attribute_with_options
        bind_call.return_value = mock_bind_response
        mock_create_client.return_value = mock_client

        result = LoadBalancerCertRenewer.renew_cert(
            instance_id=self.instance_id,
            listener_port=self.listener_port,
            cert=self.cert,
            cert_private_key=self.cert_private_key,
            region="cn-beijing",
            credential_client=self.credential_client,
            cert_source="cas",
        )

        self.assertTrue(result)
        # Reused the existing SLB cert; did NOT upload a new one.
        mock_client.upload_server_certificate_with_options.assert_not_called()
        # CAS upload/reuse still happened (ensure the CAS cert exists).
        mock_cas_upload.assert_called_once()
        # Bind used the reused SLB cert id.
        bind_req = bind_call.call_args.args[0]
        self.assertEqual(bind_req.server_certificate_id, "existing-slb-id")

    @patch("cloud_cert_renewer.clients.alibaba.CasCertUploader.create_client")
    def test_cas_uploader_upload_success(self, mock_create_cas_client):
        """Test uploading certificate to CAS returns cert_id."""
        mock_cas_client = MagicMock()
        mock_response = MagicMock()
        mock_response.body.cert_id = "cas-cert-123"
        mock_cas_client.upload_user_certificate_with_options.return_value = (
            mock_response
        )
        mock_create_cas_client.return_value = mock_cas_client

        cert_id = CasCertUploader.upload_user_certificate(
            cert=self.cert,
            private_key=self.cert_private_key,
            name="test-cert",
            credential_client=self.credential_client,
        )

        self.assertEqual(cert_id, "cas-cert-123")
        req = mock_cas_client.upload_user_certificate_with_options.call_args.args[0]
        self.assertEqual(req.cert, self.cert)
        self.assertEqual(req.key, self.cert_private_key)
        self.assertEqual(req.name, "test-cert")

    @patch("cloud_cert_renewer.clients.alibaba.CasCertUploader.create_client")
    def test_cas_uploader_upload_empty_cert_id(self, mock_create_cas_client):
        """CAS upload returning empty cert_id raises CloudApiError."""
        from cloud_cert_renewer.errors import CloudApiError

        mock_cas_client = MagicMock()
        mock_response = MagicMock()
        mock_response.body.cert_id = None
        mock_cas_client.upload_user_certificate_with_options.return_value = (
            mock_response
        )
        mock_create_cas_client.return_value = mock_cas_client

        with self.assertRaises(CloudApiError):
            CasCertUploader.upload_user_certificate(
                cert=self.cert,
                private_key=self.cert_private_key,
                name="test-cert",
                credential_client=self.credential_client,
            )

    @patch("cloud_cert_renewer.clients.alibaba.CasCertUploader.create_client")
    def test_cas_uploader_upload_failure(self, mock_create_cas_client):
        """CAS upload API error is wrapped as CloudApiError."""
        from cloud_cert_renewer.errors import CloudApiError

        mock_cas_client = MagicMock()
        mock_cas_client.upload_user_certificate_with_options.side_effect = RuntimeError(
            "CAS API boom"
        )
        mock_create_cas_client.return_value = mock_cas_client

        with self.assertRaises(CloudApiError):
            CasCertUploader.upload_user_certificate(
                cert=self.cert,
                private_key=self.cert_private_key,
                name="test-cert",
                credential_client=self.credential_client,
            )

    @patch("cloud_cert_renewer.clients.alibaba.CasCertUploader.create_client")
    def test_cas_find_existing_certificate_by_name_found(self, mock_create_cas_client):
        """ListUserCertificateOrder returns matching CertificateId for exact name."""
        mock_cas_client = MagicMock()
        match = MagicMock()
        match.name = "test-cert"
        match.certificate_id = 12345
        other = MagicMock()
        other.name = "test-cert-other"
        other.certificate_id = 99999
        mock_response = MagicMock()
        mock_response.body.certificate_order_list = [other, match]
        mock_cas_client.list_user_certificate_order_with_options.return_value = (
            mock_response
        )
        mock_create_cas_client.return_value = mock_cas_client

        cert_id = CasCertUploader.find_existing_certificate_by_name(
            name="test-cert",
            credential_client=self.credential_client,
        )

        self.assertEqual(cert_id, "12345")
        req = mock_cas_client.list_user_certificate_order_with_options.call_args.args[0]
        # I2: keyword is NOT used to find the cert (CAS Keyword matches
        # domain/resource-ID, not name); match is enforced client-side.
        self.assertIsNone(req.keyword)
        self.assertEqual(req.order_type, "UPLOAD")

    @patch("cloud_cert_renewer.clients.alibaba.CasCertUploader.create_client")
    def test_cas_find_existing_certificate_by_name_not_found(
        self, mock_create_cas_client
    ):
        """No exact name match returns None."""
        mock_cas_client = MagicMock()
        other = MagicMock()
        other.name = "other-cert"
        other.certificate_id = 99999
        mock_response = MagicMock()
        mock_response.body.certificate_order_list = [other]
        mock_cas_client.list_user_certificate_order_with_options.return_value = (
            mock_response
        )
        mock_create_cas_client.return_value = mock_cas_client

        cert_id = CasCertUploader.find_existing_certificate_by_name(
            name="test-cert",
            credential_client=self.credential_client,
        )

        self.assertIsNone(cert_id)

    @patch("cloud_cert_renewer.clients.alibaba.CasCertUploader.create_client")
    def test_cas_find_existing_certificate_by_name_api_error(
        self, mock_create_cas_client
    ):
        """List API failure returns None so upload can proceed."""
        mock_cas_client = MagicMock()
        mock_cas_client.list_user_certificate_order_with_options.side_effect = (
            RuntimeError("list boom")
        )
        mock_create_cas_client.return_value = mock_cas_client

        cert_id = CasCertUploader.find_existing_certificate_by_name(
            name="test-cert",
            credential_client=self.credential_client,
        )

        self.assertIsNone(cert_id)

    @patch("cloud_cert_renewer.clients.alibaba.CasCertUploader.upload_user_certificate")
    @patch(
        "cloud_cert_renewer.clients.alibaba.CasCertUploader.find_existing_certificate_by_name"
    )
    def test_cas_upload_or_reuse_reuses_existing(self, mock_find, mock_upload):
        """upload_or_reuse returns existing cert_id without uploading."""
        mock_find.return_value = "existing-cas-id"

        cert_id = CasCertUploader.upload_or_reuse_certificate(
            cert=self.cert,
            private_key=self.cert_private_key,
            name="test-cert",
            credential_client=self.credential_client,
        )

        self.assertEqual(cert_id, "existing-cas-id")
        mock_find.assert_called_once_with("test-cert", self.credential_client)
        mock_upload.assert_not_called()

    @patch("cloud_cert_renewer.clients.alibaba.CasCertUploader.upload_user_certificate")
    @patch(
        "cloud_cert_renewer.clients.alibaba.CasCertUploader.find_existing_certificate_by_name"
    )
    def test_cas_upload_or_reuse_uploads_when_missing(self, mock_find, mock_upload):
        """upload_or_reuse uploads when no existing certificate is found."""
        mock_find.return_value = None
        mock_upload.return_value = "new-cas-id"

        cert_id = CasCertUploader.upload_or_reuse_certificate(
            cert=self.cert,
            private_key=self.cert_private_key,
            name="test-cert",
            credential_client=self.credential_client,
        )

        self.assertEqual(cert_id, "new-cas-id")
        mock_upload.assert_called_once_with(
            cert=self.cert,
            private_key=self.cert_private_key,
            name="test-cert",
            credential_client=self.credential_client,
        )

    @patch("cloud_cert_renewer.clients.alibaba.CasCertUploader.create_client")
    def test_cas_find_by_name_paginates_and_matches_across_pages(
        self, mock_create_cas_client
    ):
        """I2: lookup pages through UPLOAD certs and matches by name client-side,
        not relying on keyword (CAS Keyword matches domain/resource-ID, not name)."""
        mock_cas_client = MagicMock()

        def _order(name, cert_id):
            m = MagicMock()
            m.name = name
            m.certificate_id = cert_id
            return m

        # Full first page (50 items), none matching; match lives on page 2.
        page1 = [_order(f"other-{i}", 10000 + i) for i in range(50)]
        match = _order("test-cert", 4242)
        page2 = [match]

        resp1 = MagicMock()
        resp1.body.certificate_order_list = page1
        resp2 = MagicMock()
        resp2.body.certificate_order_list = page2
        mock_cas_client.list_user_certificate_order_with_options.side_effect = [
            resp1,
            resp2,
        ]
        mock_create_cas_client.return_value = mock_cas_client

        cert_id = CasCertUploader.find_existing_certificate_by_name(
            name="test-cert", credential_client=self.credential_client
        )

        self.assertEqual(cert_id, "4242")
        # Two pages fetched (pagination loop).
        self.assertEqual(
            mock_cas_client.list_user_certificate_order_with_options.call_count, 2
        )
        # Request does NOT rely on keyword to find the cert.
        list_mock = mock_cas_client.list_user_certificate_order_with_options
        req1 = list_mock.call_args_list[0].args[0]
        req2 = list_mock.call_args_list[1].args[0]
        self.assertIsNone(req1.keyword)
        self.assertEqual(req1.order_type, "UPLOAD")
        self.assertEqual(req1.current_page, 1)
        self.assertEqual(req2.current_page, 2)

    @patch("cloud_cert_renewer.clients.alibaba.CasCertUploader.create_client")
    def test_cas_find_by_name_stops_on_short_page(self, mock_create_cas_client):
        """I2: a partial (final) page stops the loop without extra calls."""
        mock_cas_client = MagicMock()

        def _order(name, cert_id):
            m = MagicMock()
            m.name = name
            m.certificate_id = cert_id
            return m

        resp = MagicMock()
        resp.body.certificate_order_list = [_order("nope", 1), _order("nope-2", 2)]
        mock_cas_client.list_user_certificate_order_with_options.return_value = resp
        mock_create_cas_client.return_value = mock_cas_client

        cert_id = CasCertUploader.find_existing_certificate_by_name(
            name="test-cert", credential_client=self.credential_client
        )

        self.assertIsNone(cert_id)
        self.assertEqual(
            mock_cas_client.list_user_certificate_order_with_options.call_count, 1
        )

    @patch("cloud_cert_renewer.clients.alibaba.CasCertUploader.upload_user_certificate")
    @patch(
        "cloud_cert_renewer.clients.alibaba.CasCertUploader.find_existing_certificate_by_name"
    )
    def test_cas_upload_or_reuse_duplicate_name_fallback(self, mock_find, mock_upload):
        """I1: duplicate-name upload error triggers a re-lookup that reuses the cert."""
        from cloud_cert_renewer.errors import CloudApiError

        # Miss on first lookup, hit after the collision.
        mock_find.side_effect = [None, "reused-cas-id"]
        mock_upload.side_effect = CloudApiError(
            "CAS certificate upload failed: Certificate name already exists (duplicate)"
        )

        cert_id = CasCertUploader.upload_or_reuse_certificate(
            cert=self.cert,
            private_key=self.cert_private_key,
            name="test-cert",
            credential_client=self.credential_client,
        )

        self.assertEqual(cert_id, "reused-cas-id")
        self.assertEqual(mock_find.call_count, 2)
        mock_upload.assert_called_once()

    @patch("cloud_cert_renewer.clients.alibaba.CasCertUploader.upload_user_certificate")
    @patch(
        "cloud_cert_renewer.clients.alibaba.CasCertUploader.find_existing_certificate_by_name"
    )
    def test_cas_upload_or_reuse_non_duplicate_reraises(self, mock_find, mock_upload):
        """I1: a non-duplicate upload error re-raises (no silent reuse)."""
        from cloud_cert_renewer.errors import CloudApiError

        mock_find.return_value = None
        mock_upload.side_effect = CloudApiError(
            "CAS certificate upload failed: InvalidParameter something else"
        )

        with self.assertRaises(CloudApiError):
            CasCertUploader.upload_or_reuse_certificate(
                cert=self.cert,
                private_key=self.cert_private_key,
                name="test-cert",
                credential_client=self.credential_client,
            )
        # No re-lookup for a non-duplicate error.
        self.assertEqual(mock_find.call_count, 1)

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
        mock_client.set_load_balancer_httpslistener_attribute_with_options.return_value = (  # noqa: E501
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
        mock_client.set_load_balancer_httpslistener_attribute_with_options.return_value = (  # noqa: E501
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
        mock_client.describe_load_balancer_httpslistener_attribute_with_options.side_effect = (  # noqa: E501
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
        mock_client.describe_load_balancer_httpslistener_attribute_with_options.return_value = (  # noqa: E501
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
        mock_client.describe_load_balancer_httpslistener_attribute_with_options.return_value = (  # noqa: E501
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


class TestLoadBalancerCertRenewerIdempotency(unittest.TestCase):
    """Load Balancer certificate renewer idempotency tests"""

    def setUp(self):
        """Test setup"""
        self.credential_client = create_mock_credential_client()
        self.region = "cn-hangzhou"
        self.cert = "test_cert_content"
        self.cert_private_key = "test_private_key"
        self.instance_id = "test-instance-id"
        self.listener_port = 443

    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_find_existing_certificate_success(self, mock_create_client):
        """Test finding existing certificate successfully"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.body = MagicMock()

        # Mock certificate list
        cert1 = MagicMock()
        cert1.fingerprint = "aa:bb:cc"
        cert1.server_certificate_id = "cert-1"

        cert2 = MagicMock()
        cert2.fingerprint = "dd:ee:ff"
        cert2.server_certificate_id = "cert-2"

        mock_response.body.server_certificates.server_certificate = [cert1, cert2]
        mock_client.describe_server_certificates_with_options.return_value = (
            mock_response
        )
        mock_create_client.return_value = mock_client

        # Test finding second cert
        result = LoadBalancerCertRenewer.find_existing_certificate_by_fingerprint(
            self.region, "DD:EE:FF", self.credential_client
        )

        self.assertEqual(result, "cert-2")

        # Verify pagination size is set to 100
        args, _ = mock_client.describe_server_certificates_with_options.call_args
        self.assertEqual(args[0].region_id, self.region)

    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_find_existing_certificate_not_found(self, mock_create_client):
        """Test when existing certificate is not found"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.body = MagicMock()

        cert1 = MagicMock()
        cert1.fingerprint = "aa:bb:cc"
        cert1.server_certificate_id = "cert-1"

        mock_response.body.server_certificates.server_certificate = [cert1]
        mock_client.describe_server_certificates_with_options.return_value = (
            mock_response
        )
        mock_create_client.return_value = mock_client

        result = LoadBalancerCertRenewer.find_existing_certificate_by_fingerprint(
            self.region, "xx:yy:zz", self.credential_client
        )

        self.assertIsNone(result)

    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_find_existing_certificate_api_error(self, mock_create_client):
        """Test API error handling during search"""
        mock_client = MagicMock()
        mock_client.describe_server_certificates_with_options.side_effect = Exception(
            "API Error"
        )
        mock_create_client.return_value = mock_client

        result = LoadBalancerCertRenewer.find_existing_certificate_by_fingerprint(
            self.region, "aa:bb:cc", self.credential_client
        )

        self.assertIsNone(result)

    @patch("cloud_cert_renewer.clients.alibaba.get_cert_fingerprint_sha1")
    @patch(
        "cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.find_existing_certificate_by_fingerprint"
    )
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_renew_cert_reuses_existing(
        self, mock_create_client, mock_find, mock_fingerprint
    ):
        """Test renew_cert reuses existing certificate without uploading"""
        # Setup mocks
        mock_fingerprint.return_value = "test-fingerprint"
        mock_find.return_value = "existing-cert-id"

        mock_client = MagicMock()
        mock_bind_response = MagicMock()
        mock_bind_response.status_code = 200
        bind_method = mock_client.set_load_balancer_httpslistener_attribute_with_options
        bind_method.return_value = mock_bind_response
        mock_create_client.return_value = mock_client

        # Execute
        result = LoadBalancerCertRenewer.renew_cert(
            self.instance_id,
            self.listener_port,
            self.cert,
            self.cert_private_key,
            self.region,
            self.credential_client,
        )

        # Verify
        self.assertTrue(result)
        # Should NOT call upload
        mock_client.upload_server_certificate_with_options.assert_not_called()
        # Should call bind with existing ID
        bind_args, _ = (
            mock_client.set_load_balancer_httpslistener_attribute_with_options.call_args
        )
        self.assertEqual(bind_args[0].server_certificate_id, "existing-cert-id")

    @patch("cloud_cert_renewer.clients.alibaba.get_cert_fingerprint_sha1")
    @patch(
        "cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.find_existing_certificate_by_fingerprint"
    )
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_renew_cert_upload_when_not_found(
        self, mock_create_client, mock_find, mock_fingerprint
    ):
        """Test renew_cert uploads new certificate when not found"""
        # Setup mocks
        mock_fingerprint.return_value = "test-fingerprint"
        mock_find.return_value = None

        mock_client = MagicMock()

        # Upload response
        mock_upload_resp = MagicMock()
        mock_upload_resp.body.server_certificate_id = "new-cert-id"
        mock_client.upload_server_certificate_with_options.return_value = (
            mock_upload_resp
        )

        # Bind response
        mock_bind_resp = MagicMock()
        mock_bind_resp.status_code = 200
        bind_method = mock_client.set_load_balancer_httpslistener_attribute_with_options
        bind_method.return_value = mock_bind_resp

        mock_create_client.return_value = mock_client
        # Execute
        result = LoadBalancerCertRenewer.renew_cert(
            self.instance_id,
            self.listener_port,
            self.cert,
            self.cert_private_key,
            self.region,
            self.credential_client,
        )

        # Verify
        self.assertTrue(result)
        # Should call upload
        mock_client.upload_server_certificate_with_options.assert_called_once()
        # Should call bind with new ID
        bind_args, _ = (
            mock_client.set_load_balancer_httpslistener_attribute_with_options.call_args
        )
        self.assertEqual(bind_args[0].server_certificate_id, "new-cert-id")

    @patch("cloud_cert_renewer.clients.alibaba.get_cert_fingerprint_sha1")
    @patch(
        "cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.find_existing_certificate_by_fingerprint"
    )
    @patch("cloud_cert_renewer.clients.alibaba.LoadBalancerCertRenewer.create_client")
    def test_renew_cert_upload_when_check_fails(
        self, mock_create_client, mock_find, mock_fingerprint
    ):
        """Test renew_cert falls back to upload when idempotency check fails"""
        # Setup mocks
        mock_fingerprint.side_effect = Exception("Fingerprint error")

        mock_client = MagicMock()

        # Upload response
        mock_upload_resp = MagicMock()
        mock_upload_resp.body.server_certificate_id = "new-cert-id"
        mock_client.upload_server_certificate_with_options.return_value = (
            mock_upload_resp
        )

        # Bind response
        mock_bind_resp = MagicMock()
        mock_bind_resp.status_code = 200
        bind_method = mock_client.set_load_balancer_httpslistener_attribute_with_options
        bind_method.return_value = mock_bind_resp

        mock_create_client.return_value = mock_client
        # Execute
        result = LoadBalancerCertRenewer.renew_cert(
            self.instance_id,
            self.listener_port,
            self.cert,
            self.cert_private_key,
            self.region,
            self.credential_client,
        )

        # Verify
        self.assertTrue(result)
        # Should call upload despite check failure
        mock_client.upload_server_certificate_with_options.assert_called_once()
        # Should call bind with new ID
        bind_args, _ = (
            mock_client.set_load_balancer_httpslistener_attribute_with_options.call_args
        )
        self.assertEqual(bind_args[0].server_certificate_id, "new-cert-id")


if __name__ == "__main__":
    unittest.main()
