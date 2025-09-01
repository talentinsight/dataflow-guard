# Multi-stage Docker build for DTO API
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and README
COPY pyproject.toml README.md ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[connectors]"

# Production stage
FROM python:3.11-slim as production

# Create non-root user
RUN groupadd -r dto && useradd -r -g dto dto

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY dto_api/ ./dto_api/
COPY dto_cli/ ./dto_cli/
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Create directories for artifacts and logs
RUN mkdir -p /app/artifacts /app/logs && \
    chown -R dto:dto /app

# Switch to non-root user
USER dto

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/healthz || exit 1

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "dto_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
