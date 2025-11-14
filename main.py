import logging
import sys

from cloud_cert_renewer.cert_renewer import (
    CertRenewerFactory,
    CertValidationError,
)
from cloud_cert_renewer.config import ConfigError, load_config
from cloud_cert_renewer.container import get_container, register_service

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# CdnCertRenewer 和 LoadBalancerCertRenewer 已移至
# cloud_cert_renewer.clients.alibaba 模块


def main() -> None:
    """
    主函数：根据配置更新CDN或负载均衡器证书
    """
    try:
        # 加载配置
        config = load_config()

        # 注册配置到依赖注入容器
        container = get_container()
        register_service("config", instance=config, singleton=True)

        # 注册证书更新器工厂
        register_service(
            "cert_renewer_factory",
            instance=CertRenewerFactory,
            singleton=True,
        )

        logger.info(
            "开始更新证书: 服务类型=%s, 云服务商=%s, 鉴权方式=%s, 区域=%s, 强制更新=%s",
            config.service_type,
            config.cloud_provider,
            config.auth_method,
            (
                config.cdn_config.region
                if config.cdn_config
                else config.lb_config.region if config.lb_config else "unknown"
            ),
            config.force_update,
        )

        # 使用依赖注入容器获取证书更新器工厂
        factory = container.get("cert_renewer_factory")
        renewer = factory.create(config)
        success = renewer.renew()

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
