# Webhook Configuration

The certificate renewal system supports webhook notifications for all renewal events. This allows you to integrate with external monitoring systems, chat platforms, or custom workflows.

## Configuration

Webhook notifications are configured through environment variables:

| Variable                 | Description                                                    | Default    | Example                                        |
| ------------------------ | -------------------------------------------------------------- | ---------- | ---------------------------------------------- |
| `WEBHOOK_URL`            | Webhook endpoint URL (required to enable webhooks)             | None       | `https://hooks.slack.com/services/xxx/yyy/zzz` |
| `WEBHOOK_TIMEOUT`        | Request timeout in seconds                                     | 30         | `60`                                           |
| `WEBHOOK_RETRY_ATTEMPTS` | Number of retry attempts on failure                            | 3          | `5`                                            |
| `WEBHOOK_RETRY_DELAY`    | Initial delay between retries in seconds (exponential backoff) | 1.0        | `2.0`                                          |
| `WEBHOOK_ENABLED_EVENTS` | Comma-separated list of events to notify on                    | All events | `renewal_success,renewal_failed`               |

## Event Types

The webhook system can send notifications for the following events:

- `renewal_started` - Sent when certificate renewal begins
- `renewal_success` - Sent when certificate renewal succeeds
- `renewal_failed` - Sent when certificate renewal fails
- `renewal_skipped` - Sent when certificate is unchanged and renewal is skipped
- `batch_completed` - Sent after batch renewal completes (summary)

## Webhook Payload

All webhook notifications are sent as HTTP POST requests with a JSON payload:

```json
{
  "event_id": "uuid-v4",
  "timestamp": "2025-12-15T10:30:00Z",
  "event_type": "renewal_success",
  "source": {
    "service_type": "cdn",
    "cloud_provider": "alibaba",
    "region": "cn-hangzhou"
  },
  "target": {
    "domain_names": ["example.com"],
    "instance_ids": null,
    "listener_port": null
  },
  "certificate": {
    "fingerprint": "sha256:abcd1234...",
    "not_after": "2026-01-01T00:00:00Z",
    "not_before": "2025-01-01T00:00:00Z",
    "issuer": "Let's Encrypt"
  },
  "result": {
    "status": "success",
    "message": "Certificate renewed successfully",
    "error_code": null,
    "error_details": null,
    "retry_count": 0
  },
  "metadata": {
    "version": "0.2.2-beta1",
    "execution_time_ms": 1500,
    "total_resources": null,
    "successful_resources": null,
    "failed_resources": null,
    "force_update": false,
    "dry_run": false
  }
}
```

### Field Descriptions

- **event_id**: Unique identifier for the webhook event
- **timestamp**: When the event occurred (ISO 8601 format)
- **event_type**: Type of event (see Event Types section)
- **source**: Information about the renewal source
  - **service_type**: "cdn" or "lb"
  - **cloud_provider**: Cloud provider name
  - **region**: Cloud provider region
- **target**: Information about the target resource
  - **domain_names**: Array of domain names (for CDN)
  - **instance_ids**: Array of instance IDs (for Load Balancer)
  - **listener_port**: Listener port (for Load Balancer)
- **certificate**: Certificate information (null for batch_completed events)
  - **fingerprint**: SHA256 fingerprint of the certificate
  - **not_after**: Certificate expiration date
  - **not_before**: Certificate issue date
  - **issuer**: Certificate issuer
- **result**: Event result information
  - **status**: "success", "failure", "skipped", or "started"
  - **message**: Human-readable message
  - **error_code**: Error code (if applicable)
  - **error_details**: Detailed error information (if applicable)
- **metadata**: Additional metadata
  - **version**: Application version
  - **execution_time_ms**: Execution time in milliseconds
  - **total_resources**: Total resources (for batch_completed events)
  - **successful_resources**: Number of successful renewals (for batch_completed)
  - **failed_resources**: Number of failed renewals (for batch_completed)
  - **force_update**: Whether force update was enabled
  - **dry_run**: Whether this was a dry run

## Example Configurations

### Slack Integration

```bash
# .env file
WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
WEBHOOK_ENABLED_EVENTS=renewal_success,renewal_failed
```

### Discord Integration

```bash
# .env file
WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK
WEBHOOK_ENABLED_EVENTS=renewal_started,renewal_success,renewal_failed
```

### Custom Webhook Server

```bash
# .env file
WEBHOOK_URL=https://your-server.example.com/webhooks/cert-renewal
WEBHOOK_TIMEOUT=60
WEBHOOK_RETRY_ATTEMPTS=5
WEBHOOK_ENABLED_EVENTS=all
```

## Error Handling

- Webhook failures never block certificate renewal
- If a webhook delivery fails, it will be retried with exponential backoff
- All webhook errors are logged but don't affect the renewal process
- The system uses "best effort" delivery - failures are logged but don't stop renewals

## Security Considerations

- Webhook URLs should use HTTPS to ensure secure transmission
- Consider implementing webhook signature verification on your receiving endpoint
- The system does not currently support authentication headers, but your endpoint can use IP whitelisting
- Certificate private keys are never included in webhook payloads

## Testing

You can test webhook configuration using dry run mode:

```bash
# Enable dry run to test webhooks without actual certificate changes
DRY_RUN=true
```

Or use a webhook testing service like `webhook.site` to receive and inspect webhook payloads:

```bash
WEBHOOK_URL=https://webhook.site/your-unique-url
```

## Troubleshooting

### Webhooks Not Being Sent

1. Verify `WEBHOOK_URL` is set correctly
2. Check that the event type is enabled in `WEBHOOK_ENABLED_EVENTS`
3. Ensure your webhook endpoint is accessible and responding to POST requests

### Webhook Delivery Failures

1. Check application logs for webhook error messages
2. Verify your webhook endpoint returns 2xx status codes
3. Consider increasing `WEBHOOK_TIMEOUT` if your endpoint is slow
4. Check network connectivity to the webhook URL

### Large Payloads

Webhook payloads are typically small (1-2KB). If you're experiencing issues:

1. Check that your endpoint can handle the payload size
2. Verify that firewall rules aren't blocking large requests
3. Consider using a CDN or load balancer in front of your webhook endpoint
