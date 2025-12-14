"""Alibaba Cloud client wrapper

Provides client wrappers for Alibaba Cloud CDN and Load Balancer certificate renewal.
"""

import logging

from alibabacloud_cdn20180510 import models as cdn_20180510_models
from alibabacloud_cdn20180510.client import Client as Cdn20180510Client
from alibabacloud_credentials.client import Client as CredClient
from alibabacloud_slb20140515 import models as slb_20140515_models
from alibabacloud_slb20140515.client import Client as Slb20140515Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models

from cloud_cert_renewer.cert_renewer.base import CertValidationError
from cloud_cert_renewer.utils.ssl_cert_parser import is_cert_valid

logger = logging.getLogger(__name__)


class CdnCertRenewer:
    """CDN certificate renewer (renamed from CdnCertsRenewer)"""

    @staticmethod
    def create_client(credential_client: CredClient) -> Cdn20180510Client:
        """
        Initialize account Client using credential client
        :param credential_client: Alibaba Cloud Credentials client
            (supports access_key, sts, ram_role_arn, oidc_role_arn, etc.)
        :return: CDN Client instance
        """
        config = open_api_models.Config(credential=credential_client)
        config.endpoint = "cdn.aliyuncs.com"
        return Cdn20180510Client(config)

    @staticmethod
    def get_current_cert(
        domain_name: str,
        credential_client: CredClient,
    ) -> str | None:
        """
        Query the current certificate content configured for CDN domain
        :param domain_name: CDN domain name
        :param credential_client: Alibaba Cloud Credentials client
        :return: Certificate content (PEM format), or None if query fails or
            no certificate exists
        """
        try:
            client = CdnCertRenewer.create_client(credential_client)
            request = cdn_20180510_models.DescribeDomainCertificateInfoRequest(
                domain_name=domain_name
            )
            runtime = util_models.RuntimeOptions()
            response = client.describe_domain_certificate_info_with_options(
                request, runtime
            )

            if (
                response.body
                and response.body.cert_infos
                and response.body.cert_infos.cert_info
            ):
                cert_info = response.body.cert_infos.cert_info[0]
                server_cert = cert_info.server_certificate
                if server_cert:
                    return server_cert
            return None
        except Exception as e:
            logger.warning(
                "Failed to query CDN current certificate: %s, "
                "will skip certificate comparison",
                str(e),
            )
            return None

    @staticmethod
    def renew_cert(
        domain_name: str,
        cert: str,
        cert_private_key: str,
        region: str,
        credential_client: CredClient,
        force: bool = False,
    ) -> bool:
        """
        Update CDN domain SSL certificate
        :param domain_name: CDN domain name
        :param cert: SSL certificate content
        :param cert_private_key: SSL certificate private key
        :param region: Region
        :param credential_client: Alibaba Cloud Credentials client
        :param force: Whether to force update (update even if certificate is
            the same, for testing)
        :return: Whether successful
        """
        try:
            # Validate certificate
            if not is_cert_valid(cert, domain_name):
                raise CertValidationError(
                    f"Certificate validation failed: domain {domain_name} "
                    f"is not in the certificate or certificate has expired"
                )

            # Fingerprint comparison is handled by higher-level renewer logic
            # (e.g., BaseCertRenewer). This client only performs the update.

            # Create client
            client = CdnCertRenewer.create_client(credential_client)

            # Build request
            request = cdn_20180510_models.SetCdnDomainSSLCertificateRequest(
                domain_name=domain_name,
                cert_type="upload",
                sslprotocol="on",
                sslpub=cert,
                sslpri=cert_private_key,
                cert_region=region,
            )

            # Execute request
            runtime = util_models.RuntimeOptions()
            response = client.set_cdn_domain_sslcertificate_with_options(
                request, runtime
            )

            logger.info(
                "CDN certificate updated successfully: domain=%s, status_code=%s",
                domain_name,
                response.status_code,
            )
            return True

        except CertValidationError:
            raise
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, "message"):
                error_msg = e.message
            logger.error("CDN certificate update failed: %s", error_msg)
            data = getattr(e, "data", None)
            if data and isinstance(data, dict):
                recommend = data.get("Recommend")
                if recommend:
                    logger.error("Diagnostic URL: %s", recommend)
            raise


class LoadBalancerCertRenewer:
    """Load Balancer certificate renewer (renamed from SlbCertsRenewer)"""

    @staticmethod
    def create_client(credential_client: CredClient) -> Slb20140515Client:
        """
        Initialize account Client using credential client
        :param credential_client: Alibaba Cloud Credentials client
            (supports access_key, sts, ram_role_arn, oidc_role_arn, etc.)
        :return: SLB Client instance
        """
        config = open_api_models.Config(credential=credential_client)
        config.endpoint = "slb.aliyuncs.com"
        return Slb20140515Client(config)

    @staticmethod
    def get_listener_cert_id(
        instance_id: str,
        listener_port: int,
        region: str,
        credential_client: CredClient,
    ) -> str | None:
        """
        Query the certificate ID currently used by SLB HTTPS listener
        :param instance_id: SLB instance ID
        :param listener_port: HTTPS listener port
        :param region: Region
        :param credential_client: Alibaba Cloud Credentials client
        :return: Certificate ID, or None if query fails or listener does not exist
        """
        try:
            client = LoadBalancerCertRenewer.create_client(credential_client)
            request = (
                slb_20140515_models.DescribeLoadBalancerHTTPSListenerAttributeRequest(
                    load_balancer_id=instance_id,
                    listener_port=listener_port,
                    region_id=region,
                )
            )
            runtime = util_models.RuntimeOptions()
            response = (
                client.describe_load_balancer_https_listener_attribute_with_options(
                    request, runtime
                )
            )

            if response.body and response.body.server_certificate_id:
                return response.body.server_certificate_id
            return None
        except Exception as e:
            logger.warning(
                "Failed to query SLB listener configuration: instance_id=%s, "
                "port=%s, error=%s",
                instance_id,
                listener_port,
                str(e),
            )
            return None

    @staticmethod
    def get_current_cert_fingerprint(
        instance_id: str,
        listener_port: int,
        region: str,
        credential_client: CredClient,
    ) -> str | None:
        """
        Query the certificate fingerprint currently used by SLB instance
        :param instance_id: SLB instance ID
        :param listener_port: HTTPS listener port
        :param region: Region
        :param credential_client: Alibaba Cloud Credentials client
        :return: Certificate fingerprint (SHA1 format), or None if query fails
        """
        try:
            # First query the certificate ID used by the listener
            cert_id = LoadBalancerCertRenewer.get_listener_cert_id(
                instance_id, listener_port, region, credential_client
            )
            if not cert_id:
                return None

            # Query certificate details to get fingerprint
            client = LoadBalancerCertRenewer.create_client(credential_client)
            request = slb_20140515_models.DescribeServerCertificatesRequest(
                region_id=region,
                server_certificate_id=cert_id,
            )
            runtime = util_models.RuntimeOptions()
            response = client.describe_server_certificates_with_options(
                request, runtime
            )

            if (
                response.body
                and response.body.server_certificates
                and response.body.server_certificates.server_certificate
            ):
                certs = response.body.server_certificates.server_certificate
                if certs:
                    return certs[0].fingerprint
            return None
        except Exception as e:
            logger.warning(
                "Failed to query SLB current certificate fingerprint: %s, "
                "will skip certificate comparison",
                str(e),
            )
            return None

    @staticmethod
    def renew_cert(
        instance_id: str,
        listener_port: int,
        cert: str,
        cert_private_key: str,
        region: str,
        credential_client: CredClient,
        force: bool = False,
    ) -> bool:
        """
        Update SLB instance SSL certificate
        :param instance_id: SLB instance ID
        :param listener_port: HTTPS listener port
        :param cert: SSL certificate content
        :param cert_private_key: SSL certificate private key
        :param region: Region
        :param credential_client: Alibaba Cloud Credentials client
        :param force: Whether to force update (update even if certificate is
            the same, for testing)
        :return: Whether successful
        """
        try:
            # Fingerprint comparison is handled by higher-level renewer logic
            # (e.g., BaseCertRenewer). This client only performs the update.

            # Create client
            client = LoadBalancerCertRenewer.create_client(credential_client)

            # Build request - Upload certificate
            upload_request = slb_20140515_models.UploadServerCertificateRequest(
                server_certificate=cert,
                private_key=cert_private_key,
                region_id=region,
            )

            runtime = util_models.RuntimeOptions()
            upload_response = client.upload_server_certificate_with_options(
                upload_request, runtime
            )

            cert_id = upload_response.body.server_certificate_id
            logger.info("SLB certificate uploaded successfully: cert_id=%s", cert_id)

            # Build request - Bind certificate to listener
            # Note: SetLoadBalancerHTTPSListenerAttribute only needs to pass
            # parameters that need to be updated
            # Other parameters will keep their original values if not passed,
            # so only server_certificate_id needs to be passed
            bind_request = (
                slb_20140515_models.SetLoadBalancerHTTPSListenerAttributeRequest(
                    load_balancer_id=instance_id,
                    listener_port=listener_port,
                    region_id=region,
                    server_certificate_id=cert_id,
                )
            )

            bind_response = (
                client.set_load_balancer_https_listener_attribute_with_options(
                    bind_request, runtime
                )
            )

            logger.info(
                "SLB certificate bound successfully: instance_id=%s, "
                "port=%s, cert_id=%s, status_code=%s",
                instance_id,
                listener_port,
                cert_id,
                bind_response.status_code,
            )

            logger.info(
                "SLB certificate updated successfully: instance_id=%s, "
                "port=%s, cert_id=%s",
                instance_id,
                listener_port,
                cert_id,
            )
            return True

        except Exception as e:
            error_msg = str(e)
            if hasattr(e, "message"):
                error_msg = e.message
            logger.error("SLB certificate update failed: %s", error_msg)
            data = getattr(e, "data", None)
            if data and isinstance(data, dict):
                recommend = data.get("Recommend")
                if recommend:
                    logger.error("Diagnostic URL: %s", recommend)
            raise
