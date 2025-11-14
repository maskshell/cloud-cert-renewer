# Use Python 3.11 as base image
FROM python:3.11-slim
LABEL maintainer="analyser <analyser@gmail.com>"

# Set working directory
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml ./
COPY main.py ./
COPY cloud_cert_renewer/ ./cloud_cert_renewer/

# Install dependencies using uv
RUN uv pip install --system --no-cache -e .

# Set Python path
ENV PYTHONPATH=/app

# Run main program
CMD ["python", "main.py"]
