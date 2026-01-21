# Clinical Trial Analytics
# Multi-stage build for smaller final image

FROM python:3.11-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --all-groups --frozen

# Copy project files
COPY . .

# Install project in editable mode
RUN uv pip install -e . --quiet

# Create data directories
RUN mkdir -p data/database data/raw

# Make entrypoint executable
RUN chmod +x docker-entrypoint.sh

# Expose Jupyter port
EXPOSE 8888

ENTRYPOINT ["./docker-entrypoint.sh"]
