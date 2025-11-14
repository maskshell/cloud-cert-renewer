"""阿里云客户端封装

提供阿里云CDN和负载均衡器证书更新的客户端封装。
"""

import logging

from alibabacloud_cdn20180510 import models as cdn_20180510_models
from alibabacloud_cdn20180510.client import Client as Cdn20180510Client
from alibabacloud_slb20140515 import models as slb_20140515_models
from alibabacloud_slb20140515.client import Client as Slb20140515Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models

from cloud_cert_renewer.cert_renewer.base import CertValidationError
from cloud_cert_renewer.utils.ssl_cert_parser import (
    get_cert_fingerprint_sha1,
    get_cert_fingerprint_sha256,
    is_cert_valid,
)

logger = logging.getLogger(__name__)


class CdnCertRenewer:
    """CDN证书更新器（已重命名，原CdnCertsRenewer）"""

    @staticmethod
    def create_client(
        access_key_id: str,
        access_key_secret: str,
    ) -> Cdn20180510Client:
        """
        使用AK&SK初始化账号Client
        :param access_key_id: 云服务AccessKey ID
        :param access_key_secret: 云服务AccessKey Secret
        :return: CDN Client实例
        """
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
        )
        config.endpoint = "cdn.aliyuncs.com"
        return Cdn20180510Client(config)

    @staticmethod
    def get_current_cert(
        domain_name: str,
        access_key_id: str,
        access_key_secret: str,
    ) -> str | None:
        """
        查询CDN域名当前配置的证书内容
        :param domain_name: CDN域名
        :param access_key_id: 云服务AccessKey ID
        :param access_key_secret: 云服务AccessKey Secret
        :return: 证书内容（PEM格式），如果查询失败或没有证书则返回None
        """
        try:
            client = CdnCertRenewer.create_client(access_key_id, access_key_secret)
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
            logger.warning("查询CDN当前证书失败: %s，将跳过证书比较", str(e))
            return None

    @staticmethod
    def renew_cert(
        domain_name: str,
        cert: str,
        cert_private_key: str,
        region: str,
        access_key_id: str,
        access_key_secret: str,
        force: bool = False,
    ) -> bool:
        """
        更新CDN域名SSL证书
        :param domain_name: CDN域名
        :param cert: SSL证书内容
        :param cert_private_key: SSL证书私钥
        :param region: 区域
        :param access_key_id: 云服务AccessKey ID
        :param access_key_secret: 云服务AccessKey Secret
        :param force: 是否强制更新（即使证书相同也更新，用于测试）
        :return: 是否成功
        """
        try:
            # 验证证书
            if not is_cert_valid(cert, domain_name):
                raise CertValidationError(
                    f"证书验证失败：域名 {domain_name} 不在证书中或证书已过期"
                )

            # 查询当前证书并比较
            current_cert = CdnCertRenewer.get_current_cert(
                domain_name, access_key_id, access_key_secret
            )
            if current_cert and not force:
                new_fingerprint = get_cert_fingerprint_sha256(cert)
                current_fingerprint = get_cert_fingerprint_sha256(current_cert)
                if new_fingerprint == current_fingerprint:
                    logger.info(
                        "CDN证书未变化，跳过更新: 域名=%s, 指纹=%s",
                        domain_name,
                        new_fingerprint[:20] + "...",
                    )
                    return True
            elif force:
                logger.info(
                    "强制更新模式已启用，即使证书相同也会更新: 域名=%s", domain_name
                )

            # 创建客户端
            client = CdnCertRenewer.create_client(access_key_id, access_key_secret)

            # 构建请求
            request = cdn_20180510_models.SetCdnDomainSSLCertificateRequest(
                domain_name=domain_name,
                cert_type="upload",
                sslprotocol="on",
                sslpub=cert,
                sslpri=cert_private_key,
                cert_region=region,
            )

            # 执行请求
            runtime = util_models.RuntimeOptions()
            response = client.set_cdn_domain_sslcertificate_with_options(
                request, runtime
            )

            logger.info(
                "CDN证书更新成功: 域名=%s, 状态码=%s", domain_name, response.status_code
            )
            return True

        except CertValidationError:
            raise
        except Exception as e:
            error_msg = str(e)
            if hasattr(e, "message"):
                error_msg = e.message
            logger.error("CDN证书更新失败: %s", error_msg)
            data = getattr(e, "data", None)
            if data and isinstance(data, dict):
                recommend = data.get("Recommend")
                if recommend:
                    logger.error("诊断地址: %s", recommend)
            raise


class LoadBalancerCertRenewer:
    """负载均衡器证书更新器（已重命名，原SlbCertsRenewer）"""

    @staticmethod
    def create_client(
        access_key_id: str,
        access_key_secret: str,
    ) -> Slb20140515Client:
        """
        使用AK&SK初始化账号Client
        :param access_key_id: 云服务AccessKey ID
        :param access_key_secret: 云服务AccessKey Secret
        :return: SLB Client实例
        """
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
        )
        config.endpoint = "slb.aliyuncs.com"
        return Slb20140515Client(config)

    @staticmethod
    def get_listener_cert_id(
        instance_id: str,
        listener_port: int,
        region: str,
        access_key_id: str,
        access_key_secret: str,
    ) -> str | None:
        """
        查询SLB HTTPS监听器当前使用的证书ID
        :param instance_id: SLB实例ID
        :param listener_port: HTTPS监听器端口
        :param region: 区域
        :param access_key_id: 云服务AccessKey ID
        :param access_key_secret: 云服务AccessKey Secret
        :return: 证书ID，如果查询失败或监听器不存在则返回None
        """
        try:
            client = LoadBalancerCertRenewer.create_client(
                access_key_id, access_key_secret
            )
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
                "查询SLB监听器配置失败: 实例ID=%s, 端口=%s, 错误=%s",
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
        access_key_id: str,
        access_key_secret: str,
    ) -> str | None:
        """
        查询SLB实例当前使用的证书指纹
        :param instance_id: SLB实例ID
        :param listener_port: HTTPS监听器端口
        :param region: 区域
        :param access_key_id: 云服务AccessKey ID
        :param access_key_secret: 云服务AccessKey Secret
        :return: 证书指纹（SHA1格式），如果查询失败则返回None
        """
        try:
            # 先查询监听器使用的证书ID
            cert_id = LoadBalancerCertRenewer.get_listener_cert_id(
                instance_id, listener_port, region, access_key_id, access_key_secret
            )
            if not cert_id:
                return None

            # 查询证书详情获取指纹
            client = LoadBalancerCertRenewer.create_client(
                access_key_id, access_key_secret
            )
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
            logger.warning("查询SLB当前证书指纹失败: %s，将跳过证书比较", str(e))
            return None

    @staticmethod
    def renew_cert(
        instance_id: str,
        listener_port: int,
        cert: str,
        cert_private_key: str,
        region: str,
        access_key_id: str,
        access_key_secret: str,
        force: bool = False,
    ) -> bool:
        """
        更新SLB实例SSL证书
        :param instance_id: SLB实例ID
        :param listener_port: HTTPS监听器端口
        :param cert: SSL证书内容
        :param cert_private_key: SSL证书私钥
        :param region: 区域
        :param access_key_id: 云服务AccessKey ID
        :param access_key_secret: 云服务AccessKey Secret
        :param force: 是否强制更新（即使证书相同也更新，用于测试）
        :return: 是否成功
        """
        try:
            # 查询当前证书指纹并比较
            current_fingerprint = LoadBalancerCertRenewer.get_current_cert_fingerprint(
                instance_id, listener_port, region, access_key_id, access_key_secret
            )
            if current_fingerprint and not force:
                new_fingerprint = get_cert_fingerprint_sha1(cert)
                if new_fingerprint == current_fingerprint:
                    logger.info(
                        "SLB证书未变化，跳过更新: 实例ID=%s, 端口=%s, 指纹=%s",
                        instance_id,
                        listener_port,
                        new_fingerprint[:20] + "...",
                    )
                    return True
            elif force:
                logger.info(
                    "强制更新模式已启用，即使证书相同也会更新: 实例ID=%s, 端口=%s",
                    instance_id,
                    listener_port,
                )

            # 创建客户端
            client = LoadBalancerCertRenewer.create_client(
                access_key_id, access_key_secret
            )

            # 构建请求 - 上传证书
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
            logger.info("SLB证书上传成功: 证书ID=%s", cert_id)

            # 构建请求 - 绑定证书到监听器
            # 注意：SetLoadBalancerHTTPSListenerAttribute 只需要传递需要更新的参数
            # 其他参数如果不传递会保持原值，因此只需要传递 server_certificate_id
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
                "SLB证书绑定成功: 实例ID=%s, 端口=%s, 证书ID=%s, 状态码=%s",
                instance_id,
                listener_port,
                cert_id,
                bind_response.status_code,
            )

            logger.info(
                "SLB证书更新成功: 实例ID=%s, 端口=%s, 证书ID=%s",
                instance_id,
                listener_port,
                cert_id,
            )
            return True

        except Exception as e:
            error_msg = str(e)
            if hasattr(e, "message"):
                error_msg = e.message
            logger.error("SLB证书更新失败: %s", error_msg)
            data = getattr(e, "data", None)
            if data and isinstance(data, dict):
                recommend = data.get("Recommend")
                if recommend:
                    logger.error("诊断地址: %s", recommend)
            raise

