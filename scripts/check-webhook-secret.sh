#!/bin/bash
# Quick script to check webhook secret existence and configuration

set -e

NAMESPACE="${NAMESPACE:-devops}"
SECRET_NAME="${SECRET_NAME:-cert-renewer-webhook}"
SECRET_KEY="${SECRET_KEY:-webhook-url}"

echo "=== Checking Webhook Secret ==="
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
    echo ""
    echo "   Create it with: kubectl create namespace $NAMESPACE"
    exit 1
fi

# Check if secret exists
echo ""
echo "2. Checking secret existence..."
if kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" &>/dev/null; then
    echo "   ✓ Secret '$SECRET_NAME' exists in namespace '$NAMESPACE'"

    # Get secret details
    echo ""
    echo "3. Secret details:"
    kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o yaml | grep -A 5 "^data:" || true

    # Check if secret has the required key
    echo ""
    echo "4. Checking secret keys..."
    SECRET_KEYS=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath='{.data}' 2>/dev/null | jq -r 'keys[]' 2>/dev/null || \
        kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath='{.data}' 2>/dev/null | grep -o '"[^"]*"' | tr -d '"' || \
        echo "")

    if [ -z "$SECRET_KEYS" ]; then
        echo "   ⚠ Could not retrieve secret keys"
    elif echo "$SECRET_KEYS" | grep -q "^${SECRET_KEY}$"; then
        echo "   ✓ Secret contains key '$SECRET_KEY'"
    else
        echo "   ✗ Secret does not contain key '$SECRET_KEY'"
        echo "   Available keys:"
        echo "$SECRET_KEYS" | sed 's/^/     - /'
    fi

    # Check secret value
    echo ""
    echo "5. Checking secret value..."
    WEBHOOK_URL=$(kubectl get secret "$SECRET_NAME" -n "$NAMESPACE" -o jsonpath="{.data.${SECRET_KEY}}" 2>/dev/null | base64 -d 2>/dev/null || echo "")

    if [ -z "$WEBHOOK_URL" ]; then
        echo "   ✗ Secret value is EMPTY or key '$SECRET_KEY' does not exist"
        echo ""
        echo "   To fix, update the secret:"
        echo "   kubectl create secret generic $SECRET_NAME \\"
        echo "     --from-literal=$SECRET_KEY=https://your-webhook-url-here \\"
        echo "     --namespace=$NAMESPACE \\"
        echo "     --dry-run=client -o yaml | kubectl apply -f -"
    else
        echo "   ✓ Secret value is set"
        # Show first 30 and last 20 chars for security
        if [ ${#WEBHOOK_URL} -gt 50 ]; then
            MASKED_URL="${WEBHOOK_URL:0:30}...${WEBHOOK_URL: -20}"
        else
            MASKED_URL="${WEBHOOK_URL:0:30}..."
        fi
        echo "   Value (masked): $MASKED_URL"
        echo "   Length: ${#WEBHOOK_URL} characters"

        # Validate URL format
        echo ""
        echo "6. Validating URL format..."
        if [[ "$WEBHOOK_URL" =~ ^https?:// ]]; then
            echo "   ✓ URL format is valid (starts with http:// or https://)"
        else
            echo "   ⚠ Warning: URL does not start with http:// or https://"
            echo "   Value: ${WEBHOOK_URL:0:50}..."
        fi
    fi

else
    echo "   ✗ Secret '$SECRET_NAME' does NOT exist in namespace '$NAMESPACE'"
    echo ""
    echo "   To create the secret, run:"
    echo "   kubectl create secret generic $SECRET_NAME \\"
    echo "     --from-literal=$SECRET_KEY=https://your-webhook-url-here \\"
    echo "     --namespace=$NAMESPACE"
    echo ""
    echo "   Example for Slack:"
    echo "   kubectl create secret generic $SECRET_NAME \\"
    echo "     --from-literal=$SECRET_KEY=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \\"
    echo "     --namespace=$NAMESPACE"
    echo ""
    echo "   Example for Discord:"
    echo "   kubectl create secret generic $SECRET_NAME \\"
    echo "     --from-literal=$SECRET_KEY=https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK \\"
    echo "     --namespace=$NAMESPACE"
    exit 1
fi

echo ""
echo "=== Summary ==="
if [ -n "$WEBHOOK_URL" ] && [[ "$WEBHOOK_URL" =~ ^https?:// ]]; then
    echo "✓ Secret exists and is properly configured"
    echo ""
    echo "Next steps:"
    echo "1. Verify the webhook URL is accessible from your cluster"
    echo "2. Check if the pod has WEBHOOK_URL environment variable set"
    echo "3. Check pod logs for webhook initialization messages"
    echo ""
    echo "To check pod configuration:"
    echo "  ./scripts/diagnose-webhook.sh"
else
    echo "✗ Secret needs to be created or fixed"
fi
