"""WeChat Work message formatter

Formats webhook events into WeChat Work (企业微信) message format.
"""

from typing import Any

from cloud_cert_renewer.webhook.builders.wechat_work import (
    WeChatWorkTextMessageBuilder,
)
from cloud_cert_renewer.webhook.events import WebhookEvent
from cloud_cert_renewer.webhook.formatters.base import MessageFormatter


class WeChatWorkMessageFormatter(MessageFormatter):
    """WeChat Work message formatter

    Converts WebhookEvent to WeChat Work text message format.
    """

    def format(self, event: WebhookEvent) -> dict[str, Any]:
        """
        Format webhook event into WeChat Work text message

        :param event: Webhook event to format
        :return: WeChat Work message payload
        """
        content = self._format_event_to_text(event)
        return WeChatWorkTextMessageBuilder().set_content(content).build()

    def _format_event_to_text(self, event: WebhookEvent) -> str:
        """
        Convert webhook event to human-readable text

        :param event: Webhook event
        :return: Formatted text content
        """
        lines: list[str] = []

        # Event type and status
        event_type_display = {
            "renewal_started": "证书续期开始",
            "renewal_success": "证书续期成功",
            "renewal_failed": "证书续期失败",
            "renewal_skipped": "证书续期跳过",
            "batch_completed": "批量续期完成",
        }.get(event.event_type, event.event_type)

        lines.append(f"📋 {event_type_display}")

        # Source information
        if event.source:
            service_type_display = (
                "CDN" if event.source.service_type == "cdn" else "负载均衡"
            )
            lines.append(f"服务类型: {service_type_display}")
            lines.append(f"云服务商: {event.source.cloud_provider}")
            lines.append(f"区域: {event.source.region}")

        # Target information
        if event.target:
            if event.target.domain_names:
                domains = ", ".join(event.target.domain_names)
                lines.append(f"域名: {domains}")
            if event.target.instance_ids:
                instances = ", ".join(event.target.instance_ids)
                lines.append(f"实例ID: {instances}")
            if event.target.listener_port:
                lines.append(f"监听端口: {event.target.listener_port}")

        # Certificate information
        if event.certificate:
            if event.certificate.not_after:
                expiry_str = event.certificate.not_after.strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"证书到期时间: {expiry_str}")
            if event.certificate.issuer:
                lines.append(f"证书颁发者: {event.certificate.issuer}")

        # Result information
        if event.result:
            status_display = {
                "success": "✅ 成功",
                "failure": "❌ 失败",
                "skipped": "⏭️ 跳过",
                "started": "🔄 进行中",
            }.get(event.result.status, event.result.status)
            lines.append(f"状态: {status_display}")
            lines.append(f"消息: {event.result.message}")

            if event.result.error_code:
                lines.append(f"错误代码: {event.result.error_code}")
            if event.result.error_details:
                lines.append(f"错误详情: {event.result.error_details}")

        # Metadata
        if event.metadata:
            if event.metadata.dry_run:
                lines.append("⚠️ 这是试运行模式")
            if event.metadata.execution_time_ms:
                lines.append(f"执行时间: {event.metadata.execution_time_ms}ms")
            if event.metadata.total_resources is not None:
                lines.append(f"总资源数: {event.metadata.total_resources}")
                if event.metadata.successful_resources is not None:
                    lines.append(
                        f"成功: {event.metadata.successful_resources}, "
                        f"失败: {event.metadata.failed_resources or 0}"
                    )

        # Event ID and timestamp
        if event.event_id:
            lines.append(f"事件ID: {event.event_id}")
        if event.timestamp:
            lines.append(f"时间: {event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")

        return "\n".join(lines)
