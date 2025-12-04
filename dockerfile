# =============================================================================
# Dockerfile Inteligente - Pet Control System
# Detecta automaticamente desenvolvimento vs produção via build args
# =============================================================================
# 
# Uso:
#   Desenvolvimento: docker build -t pet-control:dev .
#   Produção:        docker build --build-arg ENV=production -t pet-control:prod .
#
# =============================================================================

# Build argument para escolher o ambiente
ARG ENV=development

# =============================================================================
# Stage 1: Build dependencies
# =============================================================================
FROM python:3.12-slim AS builder

ARG ENV

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install uv
RUN pip install --no-cache-dir uv

# Set work directory
WORKDIR /app

# Copy dependency files first (for better Docker layer caching)
COPY pyproject.toml uv.lock ./

# Install dependencies based on environment
RUN if [ "$ENV" = "production" ]; then \
        echo "🏭 Installing production dependencies (no dev packages)..." && \
        uv sync --frozen --no-dev; \
    else \
        echo "🔧 Installing all dependencies (including dev packages)..." && \
        uv sync --frozen; \
    fi

# =============================================================================
# Stage 2: Runtime image
# =============================================================================
FROM python:3.12-slim AS runtime

ARG ENV

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for production security
RUN if [ "$ENV" = "production" ]; then \
        echo "🔐 Creating non-root user for production..." && \
        groupadd -r appuser && useradd -r -g appuser appuser; \
    fi

# Set work directory
WORKDIR /app

# Copy uv and virtual environment from builder
COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv
COPY --from=builder /app/.venv /app/.venv

# Copy application files
COPY app/ ./app/
COPY main.py ./
COPY templates/ ./templates/
COPY static/ ./static/

# Copy additional development files if needed
COPY daily_check.py monthly_check.py ./

# Create necessary directories and set permissions
RUN mkdir -p uploads htmlcov logs && \
    if [ "$ENV" = "production" ]; then \
        echo "🔐 Setting production permissions..." && \
        chown -R appuser:appuser /app; \
    else \
        echo "🔧 Setting development permissions..." && \
        chmod -R 755 /app; \
    fi

# Switch to non-root user in production
USER root
RUN if [ "$ENV" = "production" ]; then \
        echo "🔐 Switching to non-root user..." && \
        su appuser; \
    fi

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV=/app/.venv

# Conditional environment variables
RUN if [ "$ENV" = "production" ]; then \
        echo "ENV ENV=production" >> /etc/environment; \
    else \
        echo "ENV ENV=development" >> /etc/environment; \
    fi

# Health check for production
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD if [ "$ENV" = "production" ]; then curl -f http://localhost:8000/health || exit 1; else exit 0; fi

# Expose port
EXPOSE 8000

# Create startup script for dynamic environment handling
RUN echo '#!/bin/bash\n\
if [ "$ENV" = "production" ]; then\n\
    echo "🚀 Starting in PRODUCTION mode with Gunicorn + 4 Uvicorn workers..."\n\
    exec uv run gunicorn main:app \\\n\
        --bind 0.0.0.0:8000 \\\n\
        --workers 4 \\\n\
        --worker-class uvicorn.workers.UvicornWorker \\\n\
        --access-logfile - \\\n\
        --error-logfile - \\\n\
        --log-level info \\\n\
        --timeout 60 \\\n\
        --graceful-timeout 30 \\\n\
        --keep-alive 5\n\
else\n\
    echo "🔧 Starting in DEVELOPMENT mode with hot reload..."\n\
    exec uv run uvicorn main:app \\\n\
        --host 0.0.0.0 \\\n\
        --port 8000 \\\n\
        --reload \\\n\
        --log-level debug\n\
fi' > /start.sh && chmod +x /start.sh

# Use JSON array format for CMD (recommended)
CMD ["/start.sh"]
