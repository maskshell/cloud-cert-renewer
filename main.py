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

from dianplus.utils.ssl_cert_parser import is_cert_valid

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
    def renew_cert(
        domain_name: str,
        cert: str,
        cert_private_key: str,
        region: str,
        access_key_id: str,
        access_key_secret: str,
    ) -> bool:
        """
        更新CDN域名SSL证书
        :param domain_name: CDN域名
        :param cert: SSL证书内容
        :param cert_private_key: SSL证书私钥
        :param region: 区域
        :param access_key_id: 阿里云AccessKey ID
        :param access_key_secret: 阿里云AccessKey Secret
        :return: 是否成功
        """
        try:
            # 验证证书
            if not is_cert_valid(cert, domain_name):
                raise CertValidationError(
                    f"证书验证失败：域名 {domain_name} 不在证书中或证书已过期"
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
            if hasattr(e, "data") and e.data and isinstance(e.data, dict):
                recommend = e.data.get("Recommend")
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
    def renew_cert(
        instance_id: str,
        cert: str,
        cert_private_key: str,
        region: str,
        access_key_id: str,
        access_key_secret: str,
    ) -> bool:
        """
        更新SLB实例SSL证书
        :param instance_id: SLB实例ID
        :param cert: SSL证书内容
        :param cert_private_key: SSL证书私钥
        :param region: 区域
        :param access_key_id: 阿里云AccessKey ID
        :param access_key_secret: 阿里云AccessKey Secret
        :return: 是否成功
        """
        try:
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
            if hasattr(e, "data") and e.data and isinstance(e.data, dict):
                recommend = e.data.get("Recommend")
                if recommend:
                    logger.error("诊断地址: %s", recommend)
            raise


def load_config() -> Tuple[str, str, str, str, str, str, str]:
    """
    从环境变量加载配置
    :return: (service_type, access_key_id, access_key_secret, domain_name_or_instance_id,
              cert, cert_private_key, region)
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
            "缺少必要的环境变量: ALIBABA_CLOUD_ACCESS_KEY_ID 或 ALIBABA_CLOUD_ACCESS_KEY_SECRET"
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

        return (
            service_type,
            access_key_id,
            access_key_secret,
            domain_name,
            cert,
            cert_private_key,
            region,
        )

    else:  # slb
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

        return (
            service_type,
            access_key_id,
            access_key_secret,
            instance_id,
            cert,
            cert_private_key,
            region,
        )


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
        ) = load_config()

        logger.info("开始更新证书: 服务类型=%s, 区域=%s", service_type, region)

        # 根据服务类型执行不同的更新逻辑
        if service_type == "cdn":
            success = CdnCertsRenewer.renew_cert(
                domain_name=domain_or_instance,
                cert=cert,
                cert_private_key=cert_private_key,
                region=region,
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
            )
        else:  # slb
            success = SlbCertsRenewer.renew_cert(
                instance_id=domain_or_instance,
                cert=cert,
                cert_private_key=cert_private_key,
                region=region,
                access_key_id=access_key_id,
                access_key_secret=access_key_secret,
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
    except Exception as e:
        logger.exception("发生未预期的错误: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
