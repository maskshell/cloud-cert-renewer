#!/bin/bash
# Diagnostic script for webhook configuration issues

set -e

NAMESPACE="${NAMESPACE:-devops}"
SECRET_NAME="${SECRET_NAME:-cert-renewer-webhook}"
SECRET_KEY="${SECRET_KEY:-webhook-url}"

echo "=== Webhook Configuration Diagnostic ==="
echo "Namespace: $NAMESPACE"
echo "Secret Name: $SECRET_NAME"
echo "Secret Key: $SECRET_KEY"
echo ""

# Check if namespace exists
echo "1. Checking namespace..."
if kubectl get namespace "$NAMESPACE" &>/dev/null; then
    echo "   ✓ Namespace '$NAMESPACE' exists"
else
    echo "   ✗ Namespace '$NAMESPACE' does not exist"
    exit 1
fi

# Check if secret exists
echo ""
echo "2. Checking secret..."
if kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" &>/dev/null; then
    echo "   ✓ Secret '$SECRET_NAME' exists"
else
    echo "   ✗ Secret '$SECRET_NAME' does not exist in namespace '$NAMESPACE'"
    echo ""
    echo "   To create the secret, run:"
    echo "   kubectl create secret generic $SECRET_NAME \\"
    echo "     --from-literal=$SECRET_KEY=https://your-webhook-url-here \\"
    echo "     --namespace=$NAMESPACE"
    exit 1
fi

# Check if secret has the required key
echo ""
echo "3. Checking secret keys..."
SECRET_KEYS=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath='{.data}' | jq -r 'keys[]' 2>/dev/null || kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath='{.data}' | grep -o '"[^"]*"' | tr -d '"')

if echo "$SECRET_KEYS" | grep -q "^${SECRET_KEY}$"; then
    echo "   ✓ Secret contains key '$SECRET_KEY'"
else
    echo "   ✗ Secret does not contain key '$SECRET_KEY'"
    echo "   Available keys: $SECRET_KEYS"
    exit 1
fi

# Check if secret value is non-empty
echo ""
echo "4. Checking secret value..."
WEBHOOK_URL=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath="{.data.${SECRET_KEY}}" | base64 -d 2>/dev/null || echo "")

if [ -z "$WEBHOOK_URL" ]; then
    echo "   ✗ Secret value is empty"
    echo ""
    echo "   To update the secret, run:"
    echo "   kubectl create secret generic $SECRET_NAME \\"
    echo "     --from-literal=$SECRET_KEY=https://your-webhook-url-here \\"
    echo "     --namespace=$NAMESPACE \\"
    echo "     --dry-run=client -o yaml | kubectl apply -f -"
    exit 1
else
    echo "   ✓ Secret value is set"
    # Mask the URL for security (show first 20 chars and last 10 chars)
    MASKED_URL="${WEBHOOK_URL:0:20}...${WEBHOOK_URL: -10}"
    echo "   Value: $MASKED_URL"
fi

# Check if webhook URL is valid
echo ""
echo "5. Validating webhook URL format..."
if [[ "$WEBHOOK_URL" =~ ^https?:// ]]; then
    echo "   ✓ Webhook URL has valid format (starts with http:// or https://)"
else
    echo "   ⚠ Warning: Webhook URL does not start with http:// or https://"
    echo "   Value: ${WEBHOOK_URL:0:50}..."
fi

# Check pod environment variables
echo ""
echo "6. Checking pod environment variables..."
POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l app.kubernetes.io/name=cloud-cert-renewer -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -z "$POD_NAME" ]; then
    echo "   ⚠ No cloud-cert-renewer pods found in namespace '$NAMESPACE'"
    echo "   This might be normal if the deployment hasn't been created yet"
else
    echo "   Found pod: $POD_NAME"

    # Check if WEBHOOK_URL env var is set in the init container
    INIT_ENV_SECRET=$(kubectl get pod "$POD_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.initContainers[?(@.name=="cert-renewer")].env[?(@.name=="WEBHOOK_URL")].valueFrom.secretKeyRef.name}' 2>/dev/null || echo "")
    INIT_ENV_KEY=$(kubectl get pod "$POD_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.initContainers[?(@.name=="cert-renewer")].env[?(@.name=="WEBHOOK_URL")].valueFrom.secretKeyRef.key}' 2>/dev/null || echo "")
    INIT_ENV_VALUE=$(kubectl get pod "$POD_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.initContainers[?(@.name=="cert-renewer")].env[?(@.name=="WEBHOOK_URL")].value}' 2>/dev/null || echo "")

    if [ -n "$INIT_ENV_SECRET" ]; then
        echo "   ✓ WEBHOOK_URL environment variable is configured in init container"
        echo "   References secret: $INIT_ENV_SECRET"
        echo "   Secret key: $INIT_ENV_KEY"

        # Verify the secret exists and has the key
        if kubectl get secret "$INIT_ENV_SECRET" -n "$NAMESPACE" &>/dev/null; then
            SECRET_VALUE=$(kubectl get secret "$INIT_ENV_SECRET" -n "$NAMESPACE" -o jsonpath="{.data.${INIT_ENV_KEY}}" 2>/dev/null | base64 -d 2>/dev/null || echo "")
            if [ -z "$SECRET_VALUE" ]; then
                echo "   ⚠ WARNING: Secret '$INIT_ENV_SECRET' exists but key '$INIT_ENV_KEY' is empty or missing"
            else
                MASKED_VALUE="${SECRET_VALUE:0:20}...${SECRET_VALUE: -10}"
                echo "   ✓ Secret value is set: $MASKED_VALUE"
            fi
        else
            echo "   ✗ ERROR: Referenced secret '$INIT_ENV_SECRET' does not exist in namespace '$NAMESPACE'"
        fi
    elif [ -n "$INIT_ENV_VALUE" ]; then
        echo "   ✓ WEBHOOK_URL environment variable is set (as literal value)"
        MASKED_VALUE="${INIT_ENV_VALUE:0:20}...${INIT_ENV_VALUE: -10}"
        echo "   Value: $MASKED_VALUE"
    else
        echo "   ✗ WEBHOOK_URL environment variable is NOT configured in init container"
        echo ""
        echo "   This means webhooks will not be sent. Check:"
        echo "   1. Helm values file has 'webhook.enabled: true'"
        echo "   2. Helm values file has 'webhook.secret.name' set correctly"
        echo "   3. The secret exists in the namespace"
        echo "   4. Helm deployment was successful"
    fi

    # Check init container logs for webhook-related messages
    echo ""
    echo "7. Checking init container logs for webhook messages..."
    LOGS=$(kubectl logs "$POD_NAME" -n "$NAMESPACE" -c cert-renewer --tail=100 2>/dev/null || echo "")

    if [ -z "$LOGS" ]; then
        echo "   ⚠ Could not retrieve logs (pod might not have run yet)"
    elif echo "$LOGS" | grep -qi "webhook"; then
        echo "   Found webhook-related log entries:"
        echo "$LOGS" | grep -i "webhook" | head -10 | sed 's/^/   /'
    else
        echo "   ⚠ No webhook-related log entries found"
        echo ""
        echo "   This indicates webhook is not being initialized. Possible causes:"
        echo "   - WEBHOOK_URL environment variable is not set in the pod"
        echo "   - WEBHOOK_URL is set but empty"
        echo "   - Webhook configuration was not loaded from environment"
        echo ""
        echo "   Check the full logs for configuration loading messages:"
        echo "   kubectl logs $POD_NAME -n $NAMESPACE -c cert-renewer | grep -i 'webhook\\|config'"
    fi
fi

echo ""
echo "=== Diagnostic Complete ==="
echo ""
echo "If all checks pass but webhooks still don't work:"
echo "1. Verify the webhook URL is accessible from the cluster"
echo "2. Check application logs: kubectl logs $POD_NAME -n $NAMESPACE -c cert-renewer"
echo "3. Test the webhook URL manually: curl -X POST '$WEBHOOK_URL' -H 'Content-Type: application/json' -d '{\"test\":\"message\"}'"
echo "4. Ensure the webhook endpoint accepts POST requests and returns 2xx status codes"
