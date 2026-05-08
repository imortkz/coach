# Multi-stage build for GymCoach backend
FROM python:3.13-slim AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first for layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# Copy application code
COPY app/ ./app/

# Run with uvicorn.
# --proxy-headers + --forwarded-allow-ips='*' tells uvicorn to honor
# X-Forwarded-Proto/X-Forwarded-For from the nginx reverse proxy. Without this,
# 307 trailing-slash redirects would be issued with scheme=http (because uvicorn
# only sees the internal http://backend:8000 connection), causing browsers to
# follow them on HTTP and lose the Authorization header / get blocked by HSTS.
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
