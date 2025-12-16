# Get uv binary from its official image
# BuildKit automatically resolves the correct architecture for the target platform
FROM ghcr.io/astral-sh/uv:latest AS uv_source

# Use Python 3.13 slim as base image
FROM python:3.13-slim
LABEL maintainer="analyser <analyser@gmail.com>"

# Set working directory
WORKDIR /app

# Install uv
COPY --from=uv_source /uv /usr/local/bin/uv

# Copy project files (excluding README.md and other non-runtime files via .dockerignore)
COPY pyproject.toml ./
COPY main.py ./
COPY cloud_cert_renewer/ ./cloud_cert_renewer/

# Install dependencies, clean caches, and set up non-root user in one layer
RUN uv pip install --system --no-cache -e . && \
    # Clean Python cache files
    find /usr/local/lib/python3.13 -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.13 -type f -name "*.pyc" -delete 2>/dev/null || true && \
    find /usr/local/lib/python3.13 -type f -name "*.pyo" -delete 2>/dev/null || true && \
    # Clean uv cache
    rm -rf /root/.cache/uv 2>/dev/null || true && \
    # Create non-root user with fixed UID/GID for consistency
    groupadd -r -g 1000 appuser && \
    useradd -r -u 1000 -g appuser -d /app -s /bin/bash appuser && \
    # Change ownership of app directory
    chown -R appuser:appuser /app && \
    # Clean apt cache to reduce image size
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set Python path
ENV PYTHONPATH=/app

# Switch to non-root user
USER appuser

# Run main program
CMD ["python", "main.py"]
