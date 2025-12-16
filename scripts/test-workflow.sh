#!/bin/bash
# Test GitHub Actions workflows locally using act
# Usage: ./scripts/test-workflow.sh [workflow-file] [job-name]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if act is installed
if ! command -v act &> /dev/null; then
    echo -e "${RED}Error: act is not installed${NC}"
    echo ""
    echo "Install act using one of the following methods:"
    echo "  macOS: brew install act"
    echo "  Linux: See https://github.com/nektos/act#installation"
    echo "  Windows: See https://github.com/nektos/act#installation"
    exit 1
fi

# Default workflow file
WORKFLOW_FILE="${1:-.github/workflows/release.yml}"
JOB_NAME="${2:-}"

# Check if workflow file exists
if [ ! -f "$WORKFLOW_FILE" ]; then
    echo -e "${RED}Error: Workflow file not found: $WORKFLOW_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}Testing GitHub Actions workflow locally${NC}"
echo "Workflow: $WORKFLOW_FILE"
if [ -n "$JOB_NAME" ]; then
    echo "Job: $JOB_NAME"
fi
echo ""

# Check if .secrets file exists
if [ ! -f ".secrets" ]; then
    echo -e "${YELLOW}Warning: .secrets file not found${NC}"
    echo "Create .secrets file from .secrets.example if you need secrets for testing"
    echo ""
fi

# Build act command
ACT_CMD="act workflow_dispatch"

# Add job filter if specified
if [ -n "$JOB_NAME" ]; then
    ACT_CMD="$ACT_CMD --job $JOB_NAME"
fi

# Add workflow file
ACT_CMD="$ACT_CMD --workflows $WORKFLOW_FILE"

# Add secrets file if it exists
if [ -f ".secrets" ]; then
    ACT_CMD="$ACT_CMD --secret-file .secrets"
fi

# Add event payload if it exists
if [ -f ".github/workflows/payload.json" ]; then
    ACT_CMD="$ACT_CMD --eventpath .github/workflows/payload.json"
fi

# Run act
echo -e "${GREEN}Running act...${NC}"
echo "Command: $ACT_CMD"
echo ""

eval $ACT_CMD
