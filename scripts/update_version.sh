#!/bin/bash
# Update version across all files in the project
# Usage: ./scripts/update_version.sh <version>
# Example: ./scripts/update_version.sh 0.1.0

set -e

VERSION="${1:-}"

if [ -z "$VERSION" ]; then
    echo "Error: Version is required"
    echo "Usage: $0 <version>"
    echo "Example: $0 0.1.0"
    exit 1
fi

# Validate version format (semantic versioning)
if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.-]+)?$ ]]; then
    echo "Error: Invalid version format. Expected semantic version (e.g., 0.1.0 or 0.1.0-rc.1)"
    exit 1
fi

echo "Updating version to $VERSION..."

# Update pyproject.toml
if [ -f "pyproject.toml" ]; then
    sed -i.bak "s/^version = \".*\"/version = \"$VERSION\"/" pyproject.toml
    rm -f pyproject.toml.bak
    echo "✓ Updated pyproject.toml"
else
    echo "Warning: pyproject.toml not found"
fi

# Update __init__.py
if [ -f "cloud_cert_renewer/__init__.py" ]; then
    sed -i.bak "s/^__version__ = \".*\"/__version__ = \"$VERSION\"/" cloud_cert_renewer/__init__.py
    rm -f cloud_cert_renewer/__init__.py.bak
    echo "✓ Updated cloud_cert_renewer/__init__.py"
else
    echo "Warning: cloud_cert_renewer/__init__.py not found"
fi

# Update Chart.yaml
if [ -f "helm/cloud-cert-renewer/Chart.yaml" ]; then
    sed -i.bak "s/^version: .*/version: $VERSION/" helm/cloud-cert-renewer/Chart.yaml
    sed -i.bak "s/^appVersion: .*/appVersion: \"$VERSION\"/" helm/cloud-cert-renewer/Chart.yaml
    rm -f helm/cloud-cert-renewer/Chart.yaml.bak
    echo "✓ Updated helm/cloud-cert-renewer/Chart.yaml"
else
    echo "Warning: helm/cloud-cert-renewer/Chart.yaml not found"
fi

# Update CHANGELOG.md
if [ -f "CHANGELOG.md" ]; then
    # Get current date in YYYY-MM-DD format
    RELEASE_DATE=$(date +%Y-%m-%d)

    # Check if [Unreleased] section exists
    if grep -q "^## \[Unreleased\]" CHANGELOG.md; then
        # Replace [Unreleased] with version and date
        # Use a temporary file to handle the replacement safely
        sed -i.bak "s/^## \[Unreleased\]/## [$VERSION] - $RELEASE_DATE/" CHANGELOG.md
        rm -f CHANGELOG.md.bak
        echo "✓ Updated CHANGELOG.md: Replaced [Unreleased] with [$VERSION] - $RELEASE_DATE"

        # Add new [Unreleased] section at the top (after the header)
        # Find the line number of the first version entry
        FIRST_VERSION_LINE=$(grep -n "^## \[" CHANGELOG.md | head -1 | cut -d: -f1)
        if [ -n "$FIRST_VERSION_LINE" ]; then
            # Insert [Unreleased] section before the first version entry
            sed -i.bak "${FIRST_VERSION_LINE}i\\
## [Unreleased]\\
" CHANGELOG.md
            rm -f CHANGELOG.md.bak
            echo "✓ Added new [Unreleased] section to CHANGELOG.md"
        fi
    else
        echo "Warning: [Unreleased] section not found in CHANGELOG.md, skipping CHANGELOG update"
    fi
else
    echo "Warning: CHANGELOG.md not found"
fi

# Update uv.lock
if command -v uv &> /dev/null; then
    echo "Updating uv.lock..."
    uv lock
    echo "✓ Updated uv.lock"
else
    echo "Warning: uv command not found, skipping uv.lock update"
    echo "  Please run 'uv lock' manually after updating versions"
fi

# Verify version consistency
echo ""
echo "Verifying version consistency..."

PYPROJECT_VERSION=$(grep '^version =' pyproject.toml 2>/dev/null | sed 's/version = "\(.*\)"/\1/' || echo "")
INIT_VERSION=$(grep '^__version__ =' cloud_cert_renewer/__init__.py 2>/dev/null | sed 's/__version__ = "\(.*\)"/\1/' || echo "")
CHART_VERSION=$(grep '^version:' helm/cloud-cert-renewer/Chart.yaml 2>/dev/null | sed 's/version: //' || echo "")
CHART_APP_VERSION=$(grep '^appVersion:' helm/cloud-cert-renewer/Chart.yaml 2>/dev/null | sed 's/appVersion: "\(.*\)"/\1/' || echo "")

if [ "$PYPROJECT_VERSION" = "$VERSION" ] && [ "$INIT_VERSION" = "$VERSION" ] && [ "$CHART_VERSION" = "$VERSION" ] && [ "$CHART_APP_VERSION" = "$VERSION" ]; then
    echo "✓ All versions are consistent: $VERSION"
    exit 0
else
    echo "Error: Version mismatch detected!"
    echo "  pyproject.toml: $PYPROJECT_VERSION"
    echo "  __init__.py: $INIT_VERSION"
    echo "  Chart.yaml version: $CHART_VERSION"
    echo "  Chart.yaml appVersion: $CHART_APP_VERSION"
    echo "  Expected: $VERSION"
    exit 1
fi
