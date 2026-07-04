# Use the official uv image as builder
FROM python:3.13-slim-bookworm AS builder

# Install uv via pip instead of pulling from ghcr.io
RUN pip install --no-cache-dir uv

WORKDIR /app

# Enable uv compile cache for faster builds
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies (into the uv virtualenv, not system Python)
RUN uv sync --frozen --no-install-project --no-dev

# Download the model during build (zero network at runtime)
COPY download_model.py ./
ARG MEMORY_GENERATOR_MODEL=Qwen/Qwen3-Embedding-0.6B
ENV MEMORY_GENERATOR_MODEL=${MEMORY_GENERATOR_MODEL}

RUN .venv/bin/python download_model.py

# Copy application code
COPY src/ ./src/

# Final install of the project itself
RUN uv sync --frozen --no-dev

# --- Runtime stage ---
FROM python:3.13-slim-bookworm AS runtime

# Install uv via pip instead of pulling from ghcr.io
RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy the pre-built virtual environment from builder
# uv creates .venv by default in /app
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/models /app/models
COPY .env /app/.env

# Ensure .venv is used
ENV PATH="/app/.venv/bin:$PATH"

# Copy only necessary code (the venv has the package installed already)
COPY --from=builder /app/src /app/src

# Alibaba Cloud Function Compute requires port 9000
# ECS/ECI/ACK can override with PORT env var
EXPOSE 8000

# Use the installed script from pyproject.toml [project.scripts]
CMD ["llm-server"]

