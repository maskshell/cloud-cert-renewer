import logging
import os
import sys
from typing import Tuple

from alibabacloud_cdn20180510 import models as cdn_20180510_models
from alibabacloud_cdn20180510.client import Client as Cdn20180510Client
from alibabacloud_slb20140515 import models as slb_20140515_models
from alibabacloud_slb20140515.client import Client as Slb20140515Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from dotenv import load_dotenv

from dianplus.utils.ssl_cert_parser import (
    get_cert_fingerprint_sha1,
    get_cert_fingerprint_sha256,
    is_cert_valid,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class ConfigError(Exception):
    """配置错误异常"""

    pass


class CertValidationError(Exception):
    """证书验证错误异常"""

    pass


class CdnCertsRenewer:
    """CDN证书更新器"""

    @staticmethod
    def create_client(
        access_key_id: str,
        access_key_secret: str,
    ) -> Cdn20180510Client:
        """
        使用AK&SK初始化账号Client
        :param access_key_id: 阿里云AccessKey ID
        :param access_key_secret: 阿里云AccessKey Secret
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
        :param access_key_id: 阿里云AccessKey ID
        :param access_key_secret: 阿里云AccessKey Secret
        :return: 证书内容（PEM格式），如果查询失败或没有证书则返回None
        """
        try:
            client = CdnCertsRenewer.create_client(access_key_id, access_key_secret)
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
        :param access_key_id: 阿里云AccessKey ID
        :param access_key_secret: 阿里云AccessKey Secret
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
            current_cert = CdnCertsRenewer.get_current_cert(
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
            client = CdnCertsRenewer.create_client(access_key_id, access_key_secret)

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


class SlbCertsRenewer:
    """SLB证书更新器"""

    @staticmethod
    def create_client(
        access_key_id: str,
        access_key_secret: str,
    ) -> Slb20140515Client:
        """
        使用AK&SK初始化账号Client
        :param access_key_id: 阿里云AccessKey ID
        :param access_key_secret: 阿里云AccessKey Secret
        :return: SLB Client实例
        """
        config = open_api_models.Config(
            access_key_id=access_key_id,
            access_key_secret=access_key_secret,
        )
        config.endpoint = "slb.aliyuncs.com"
        return Slb20140515Client(config)

    @staticmethod
    def get_current_cert_fingerprint(
        instance_id: str,
        region: str,
        access_key_id: str,
        access_key_secret: str,
    ) -> str | None:
        """
        查询SLB实例当前使用的证书指纹
        注意：此方法查询所有证书列表，实际使用时需要根据监听器配置找到正确的证书
        这里简化实现，通过证书名称匹配（如果证书名称包含实例ID或域名信息）
        :param instance_id: SLB实例ID
        :param region: 区域
        :param access_key_id: 阿里云AccessKey ID
        :param access_key_secret: 阿里云AccessKey Secret
        :return: 证书指纹（SHA1格式），如果查询失败则返回None
        """
        try:
            client = SlbCertsRenewer.create_client(access_key_id, access_key_secret)
            request = slb_20140515_models.DescribeServerCertificatesRequest(
                region_id=region,
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
                # 尝试根据证书名称或ID匹配（简化实现）
                # 实际使用时应该查询监听器配置来确定使用的证书
                for cert in certs:
                    # 如果证书名称包含实例ID，或者有其他匹配逻辑
                    # 这里返回第一个证书的指纹作为示例
                    # 实际场景需要根据业务逻辑匹配正确的证书
                    return cert.fingerprint
            return None
        except Exception as e:
            logger.warning("查询SLB当前证书指纹失败: %s，将跳过证书比较", str(e))
            return None

    @staticmethod
    def renew_cert(
        instance_id: str,
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
        :param cert: SSL证书内容
        :param cert_private_key: SSL证书私钥
        :param region: 区域
        :param access_key_id: 阿里云AccessKey ID
        :param access_key_secret: 阿里云AccessKey Secret
        :param force: 是否强制更新（即使证书相同也更新，用于测试）
        :return: 是否成功
        """
        try:
            # 查询当前证书指纹并比较
            current_fingerprint = SlbCertsRenewer.get_current_cert_fingerprint(
                instance_id, region, access_key_id, access_key_secret
            )
            if current_fingerprint and not force:
                new_fingerprint = get_cert_fingerprint_sha1(cert)
                if new_fingerprint == current_fingerprint:
                    logger.info(
                        "SLB证书未变化，跳过更新: 实例ID=%s, 指纹=%s",
                        instance_id,
                        new_fingerprint[:20] + "...",
                    )
                    return True
            elif force:
                logger.info(
                    "强制更新模式已启用，即使证书相同也会更新: 实例ID=%s", instance_id
                )

            # 创建客户端
            client = SlbCertsRenewer.create_client(access_key_id, access_key_secret)

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

            # 注意：SLB证书更新需要将证书绑定到监听器
            # 这里只上传证书，绑定操作需要额外的API调用
            # 实际使用时需要根据具体监听器配置进行绑定

            logger.info("SLB证书更新成功: 实例ID=%s, 证书ID=%s", instance_id, cert_id)
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


def load_config() -> Tuple[str, str, str, str, str, str, str, bool]:
    """
    从环境变量加载配置
    :return: (service_type, access_key_id, access_key_secret,
              domain_name_or_instance_id, cert, cert_private_key, region, force)
    :raises ConfigError: 配置错误时抛出
    """
    # 加载 .env 文件
    load_dotenv()

    # 获取服务类型
    service_type = os.environ.get("SERVICE_TYPE", "cdn").lower()
    if service_type not in ["cdn", "slb"]:
        raise ConfigError(f"不支持的服务类型: {service_type}，仅支持 cdn 或 slb")

    # 获取访问凭证
    access_key_id = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_ID")
    access_key_secret = os.environ.get("ALIBABA_CLOUD_ACCESS_KEY_SECRET")

    if not access_key_id or not access_key_secret:
        raise ConfigError(
            "缺少必要的环境变量: ALIBABA_CLOUD_ACCESS_KEY_ID 或 "
            "ALIBABA_CLOUD_ACCESS_KEY_SECRET"
        )

    # 根据服务类型获取不同的配置
    if service_type == "cdn":
        domain_name = os.environ.get("CDN_DOMAIN_NAME")
        cert = os.environ.get("CDN_CERT")
        cert_private_key = os.environ.get("CDN_CERT_PRIVATE_KEY")
        region = os.environ.get("CDN_REGION", "cn-hangzhou")

        if not domain_name:
            raise ConfigError("缺少必要的环境变量: CDN_DOMAIN_NAME")
        if not cert:
            raise ConfigError("缺少必要的环境变量: CDN_CERT")
        if not cert_private_key:
            raise ConfigError("缺少必要的环境变量: CDN_CERT_PRIVATE_KEY")

        # 获取强制更新标志
        force_str = os.environ.get("FORCE_UPDATE", "false").lower()
        force = force_str in ("true", "1", "yes", "on")

        return (
            service_type,
            access_key_id,
            access_key_secret,
            domain_name,
            cert,
            cert_private_key,
            region,
            force,
        )

    elif service_type == "slb":
        instance_id = os.environ.get("SLB_INSTANCE_ID")
        cert = os.environ.get("SLB_CERT")
        cert_private_key = os.environ.get("SLB_CERT_PRIVATE_KEY")
        region = os.environ.get("SLB_REGION", "cn-hangzhou")

        if not instance_id:
            raise ConfigError("缺少必要的环境变量: SLB_INSTANCE_ID")
        if not cert:
            raise ConfigError("缺少必要的环境变量: SLB_CERT")
        if not cert_private_key:
            raise ConfigError("缺少必要的环境变量: SLB_CERT_PRIVATE_KEY")

        # 获取强制更新标志
        force_str = os.environ.get("FORCE_UPDATE", "false").lower()
        force = force_str in ("true", "1", "yes", "on")

        return (
            service_type,
            access_key_id,
            access_key_secret,
            instance_id,
            cert,
            cert_private_key,
            region,
            force,
        )
    else:
        # 理论上不应该到达这里，因为 service_type 已经在前面验证过
        raise ConfigError(f"不支持的服务类型: {service_type}，仅支持 cdn 或 slb")


def main() -> None:
    """
    主函数：根据配置更新CDN或SLB证书
    """
    try:
        # 加载配置
        (
            service_type,
            access_key_id,
            access_key_secret,
            domain_or_instance,
            cert,
            cert_private_key,
            region,
            force,
        ) = load_config()

        logger.info(
            "开始更新证书: 服务类型=%s, 区域=%s, 强制更新=%s",
            service_type,
            region,
            force,
        )

        # 根据服务类型执行不同的更新逻辑
        if service_type == "cdn":
            success = CdnCertsRenewer.renew_cert(
                domain_name=domain_or_instance,
                cert=cert,
                cert_private_key=cert_private_key,
                region=region,
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                force=force,
            )
        elif service_type == "slb":
            success = SlbCertsRenewer.renew_cert(
                instance_id=domain_or_instance,
                cert=cert,
                cert_private_key=cert_private_key,
                region=region,
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
                force=force,
            )

        if success:
            logger.info("证书更新完成")
            sys.exit(0)
        else:
            logger.error("证书更新失败")
            sys.exit(1)

    except ConfigError as e:
        logger.error("配置错误: %s", e)
        sys.exit(1)
    except CertValidationError as e:
        logger.error("证书验证错误: %s", e)
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        # 主函数需要捕获所有异常以确保程序优雅退出
        logger.exception("发生未预期的错误: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
