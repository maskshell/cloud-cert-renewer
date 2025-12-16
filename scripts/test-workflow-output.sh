#!/bin/bash
# Test script to verify GitHub Actions output handling with heredoc
# This simulates the problematic pattern to ensure it works correctly

set -e

# Simulate the custom registry section generation
REGISTRY_URL="registry.example.com"
REGISTRY_IMAGE="my-image"
VERSION="0.2.6-beta6"
TAG="v0.2.6-beta6"

CUSTOM_SECTION="**Custom Registry:**
- \`${REGISTRY_URL}/${REGISTRY_IMAGE}:${VERSION}\`
- \`${REGISTRY_URL}/${REGISTRY_IMAGE}:${TAG}\`
- \`${REGISTRY_URL}/${REGISTRY_IMAGE}:latest\`

"

# Test the fixed pattern
TEST_OUTPUT="/tmp/test_github_output.txt"
rm -f "$TEST_OUTPUT"

{
  echo "section<<CUSTOM_SECTION_EOF"
  printf '%s' "$CUSTOM_SECTION"
  echo ""
  echo "CUSTOM_SECTION_EOF"
} >> "$TEST_OUTPUT"

echo "Test output written to: $TEST_OUTPUT"
echo ""
echo "Content:"
cat "$TEST_OUTPUT"
echo ""
echo "Verifying heredoc delimiter..."
if grep -q "CUSTOM_SECTION_EOF" "$TEST_OUTPUT"; then
  echo "✅ Heredoc delimiter found correctly"
else
  echo "❌ Heredoc delimiter not found"
  exit 1
fi

# Check that delimiter is on its own line
if grep -q "^CUSTOM_SECTION_EOF$" "$TEST_OUTPUT"; then
  echo "✅ Delimiter is on its own line"
else
  echo "❌ Delimiter is not on its own line"
  exit 1
fi

echo ""
echo "✅ All tests passed!"
