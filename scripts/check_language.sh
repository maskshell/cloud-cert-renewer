#!/bin/bash
# Language policy checker for pre-commit hook
# Checks for non-English content in code and documentation files

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Files to check (Python, Markdown, YAML, YML)
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(py|md|yaml|yml)$' || true)

if [ -z "$FILES" ]; then
    exit 0
fi

# Check for Chinese characters (CJK Unified Ideographs)
ERRORS=0
WARNINGS=0

for file in $FILES; do
    # Skip excluded files
    if [[ "$file" =~ ^(helm/|\.pytest_cache/|__pycache__/) ]]; then
        continue
    fi
    
    # Check for Chinese characters (Unicode range: \u4e00-\u9fff)
    if grep -P "[\u4e00-\u9fff]" "$file" > /dev/null 2>&1; then
        # Check if it's in an exception context
        # 1. Check if it's in a string marked as non-English content
        # 2. Check if it's in a comment explaining it's an exception
        # 3. Check if it's test data
        
        # For now, we'll flag it and let the developer decide
        # In a real implementation, you might want more sophisticated detection
        
        # Check if file contains exception markers
        if grep -iE "(translation|i18n|multilingual|test data|example|例外|exception)" "$file" > /dev/null 2>&1; then
            echo -e "${YELLOW}Warning:${NC} $file contains Chinese characters, but may be in an exception context"
            WARNINGS=$((WARNINGS + 1))
        else
            echo -e "${RED}Error:${NC} $file contains Chinese characters (non-English content detected)"
            echo "   Please ensure all content follows the English language policy."
            echo "   See CONTRIBUTING.md for details."
            ERRORS=$((ERRORS + 1))
        fi
    fi
done

if [ $ERRORS -gt 0 ]; then
    echo -e "\n${RED}Language policy check failed!${NC}"
    echo "Please review the files above and ensure all content is in English."
    echo "Exceptions are allowed for:"
    echo "  - Proper nouns (brand names, etc.)"
    echo "  - Test data"
    echo "  - Explicitly designated non-English content"
    exit 1
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "\n${YELLOW}Language policy check passed with warnings.${NC}"
    echo "Please verify that the Chinese characters are in allowed exception contexts."
    exit 0
fi

echo -e "${GREEN}Language policy check passed!${NC}"
exit 0

