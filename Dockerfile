# ============================================
# EducAgent Multi-Stage Dockerfile
# ============================================
# This Dockerfile builds a production-ready image for EducAgent
# containing both the FastAPI backend and Next.js frontend
#
# Build: docker compose build
# Run:   docker compose up -d
#
# Prerequisites:
#   1. Copy .env.example to .env and configure your API keys
#   2. Optionally customize config/main.yaml
# ============================================

# ============================================
# Stage 1: Frontend Builder
# ============================================
FROM node:22-slim AS frontend-builder

WORKDIR /app/web

# Accept build argument for backend port
ARG BACKEND_PORT=8001

# Copy package files first for better caching
COPY web/package.json web/package-lock.json* ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy frontend source code
COPY web/ ./

# Create .env.local with placeholder that will be replaced at runtime
# Use a unique placeholder that can be safely replaced
RUN echo "NEXT_PUBLIC_API_BASE=__NEXT_PUBLIC_API_BASE_PLACEHOLDER__" > .env.local

# Build Next.js for production with standalone output
# This allows runtime environment variable injection
RUN npm run build

# ============================================
# Stage 2: Python Base with Dependencies
# ============================================
# RAG_PROVIDER controls which optional heavy ML packages are installed:
#   lightrag (default) — no extra installs
#   llamaindex         — installs llama-index
#   raganything        — installs raganything (MinerU parser)
#   raganything_docling — installs raganything + docling (PyTorch, transformers)
ARG RAG_PROVIDER=lightrag

FROM python:3.11-slim AS python-base

ARG RAG_PROVIDER

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
# libgl1 and libglib2.0-0 are required for OpenCV (used by raganything/MinerU)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Install RAG pipeline dependencies based on RAG_PROVIDER
RUN if [ "$RAG_PROVIDER" = "llamaindex" ]; then \
        pip install llama-index; \
    elif [ "$RAG_PROVIDER" = "raganything" ]; then \
        pip install raganything; \
    elif [ "$RAG_PROVIDER" = "raganything_docling" ]; then \
        pip install raganything docling; \
    fi

# ============================================
# Stage 3: Production Image
# ============================================
FROM python:3.11-slim AS production

ARG RAG_PROVIDER=lightrag

# Labels
LABEL maintainer="EducAgent Team" \
      description="EducAgent: AI-Powered Personalized Learning Assistant" \
      version="0.1.0"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    NODE_ENV=production \
    # Default ports (can be overridden)
    BACKEND_PORT=8001 \
    FRONTEND_PORT=3782 \
    RAG_PROVIDER=${RAG_PROVIDER}

WORKDIR /app

# Install system dependencies
# Note: libgl1 and libglib2.0-0 are required for OpenCV (used by mineru)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    bash \
    supervisor \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Node.js from frontend-builder stage (avoids re-downloading from NodeSource)
COPY --from=frontend-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=frontend-builder /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -sf /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -sf /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
    && node --version && npm --version

# Copy Python packages from builder stage
COPY --from=python-base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-base /usr/local/bin /usr/local/bin

# Copy built frontend from frontend-builder stage (standalone output)
# .next/standalone is self-contained with a minimal node_modules — no full copy needed
COPY --from=frontend-builder /app/web/.next/standalone ./web/
COPY --from=frontend-builder /app/web/.next/static ./web/.next/static
COPY --from=frontend-builder /app/web/public ./web/public

# Copy application source code
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY pyproject.toml ./
COPY requirements.txt ./
COPY alembic.ini ./

# Create necessary directories (these will be overwritten by volume mounts)
RUN mkdir -p \
    data/user/solve \
    data/user/question \
    data/user/research/cache \
    data/user/research/reports \
    data/user/guide \
    data/user/notebook \
    data/user/co-writer/audio \
    data/user/co-writer/tool_calls \
    data/user/logs \
    data/user/run_code_workspace \
    data/user/performance \
    data/knowledge_bases

# Create supervisord configuration for running both services
# Log output goes to stdout/stderr so docker logs can capture them
RUN mkdir -p /etc/supervisor/conf.d

RUN cat > /etc/supervisor/conf.d/educagent.conf <<'EOF'
[supervisord]
nodaemon=true
logfile=/dev/null
logfile_maxbytes=0
pidfile=/var/run/supervisord.pid

[program:backend]
command=/bin/bash /app/start-backend.sh
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0
environment=PYTHONPATH="/app",PYTHONUNBUFFERED="1"

[program:frontend]
command=/bin/bash /app/start-frontend.sh
directory=/app/web
autostart=true
autorestart=true
startsecs=5
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0
environment=NODE_ENV="production"
EOF

RUN sed -i 's/\r$//' /etc/supervisor/conf.d/educagent.conf

# Create backend startup script
RUN cat > /app/start-backend.sh <<'EOF'
#!/bin/bash
set -e

BACKEND_PORT=${BACKEND_PORT:-8001}

echo "[Backend]  🚀 Starting FastAPI backend on port ${BACKEND_PORT}..."

# Run uvicorn directly - the application's logging system already handles:
# 1. Console output (visible in docker logs)
# 2. File logging to data/user/logs/ai_tutor_*.log
exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${BACKEND_PORT}
EOF

RUN sed -i 's/\r$//' /app/start-backend.sh && chmod +x /app/start-backend.sh

# Create frontend startup script
# This script handles runtime environment variable injection for Next.js
RUN cat > /app/start-frontend.sh <<'EOF'
#!/bin/bash
set -e

# Get the backend port (default to 8001)
BACKEND_PORT=${BACKEND_PORT:-8001}
FRONTEND_PORT=${FRONTEND_PORT:-3782}

# Determine the API base URL with multiple fallback options
# Priority: NEXT_PUBLIC_API_BASE_EXTERNAL > NEXT_PUBLIC_API_BASE > auto-detect
if [ -n "$NEXT_PUBLIC_API_BASE_EXTERNAL" ]; then
    # Explicit external URL for cloud deployments
    API_BASE="$NEXT_PUBLIC_API_BASE_EXTERNAL"
    echo "[Frontend] 📌 Using external API URL: ${API_BASE}"
elif [ -n "$NEXT_PUBLIC_API_BASE" ]; then
    # Custom API base URL
    API_BASE="$NEXT_PUBLIC_API_BASE"
    echo "[Frontend] 📌 Using custom API URL: ${API_BASE}"
else
    # Default: localhost with configured backend port
    # Note: This only works for local development, not cloud deployments
    API_BASE="http://localhost:${BACKEND_PORT}"
    echo "[Frontend] 📌 Using default API URL: ${API_BASE}"
    echo "[Frontend] ⚠️  For cloud deployment, set NEXT_PUBLIC_API_BASE_EXTERNAL to your server's public URL"
    echo "[Frontend]    Example: -e NEXT_PUBLIC_API_BASE_EXTERNAL=https://your-server.com:${BACKEND_PORT}"
fi

echo "[Frontend] 🚀 Starting Next.js frontend on port ${FRONTEND_PORT}..."

# Replace placeholder in built Next.js files
# This is necessary because NEXT_PUBLIC_* vars are inlined at build time
find /app/web/.next -type f \( -name "*.js" -o -name "*.json" \) -exec \
    sed -i "s|__NEXT_PUBLIC_API_BASE_PLACEHOLDER__|${API_BASE}|g" {} \; 2>/dev/null || true

# Also update .env.local for any runtime reads
echo "NEXT_PUBLIC_API_BASE=${API_BASE}" > /app/web/.env.local

# Start Next.js standalone server
HOSTNAME=0.0.0.0 PORT=${FRONTEND_PORT} exec node /app/web/server.js
EOF

RUN sed -i 's/\r$//' /app/start-frontend.sh && chmod +x /app/start-frontend.sh

# Create entrypoint script
RUN cat > /app/entrypoint.sh <<'EOF'
#!/bin/bash
set -e

echo "============================================"
echo "🚀 Starting EducAgent"
echo "============================================"

# Set default ports if not provided
export BACKEND_PORT=${BACKEND_PORT:-8001}
export FRONTEND_PORT=${FRONTEND_PORT:-3782}

echo "📌 Backend Port: ${BACKEND_PORT}"
echo "📌 Frontend Port: ${FRONTEND_PORT}"

# Check for required environment variables
if [ -z "$LLM_API_KEY" ]; then
    echo "⚠️  Warning: LLM_API_KEY not set"
    echo "   Please provide LLM configuration via environment variables or .env file"
fi

if [ -z "$LLM_MODEL" ]; then
    echo "⚠️  Warning: LLM_MODEL not set"
    echo "   Please configure LLM_MODEL in your .env file"
fi

# Initialize user data directories if empty
echo "📁 Checking data directories..."
if [ ! -f "/app/data/user/user_history.json" ]; then
    echo "   Initializing user data directories..."
    python -c "
from pathlib import Path
from src.services.setup import init_user_directories
init_user_directories(Path('/app'))
" 2>/dev/null || echo "   ⚠️ Directory initialization skipped (will be created on first use)"
fi

echo "============================================"
echo "📦 Configuration loaded from:"
echo "   - Environment variables (.env file)"
echo "   - config/main.yaml"
echo "   - config/agents.yaml"
echo "============================================"

# Ensure log directory exists and is writable (survives volume-mount overrides)
mkdir -p /app/data/user/logs
chmod 777 /app/data/user/logs 2>/dev/null || true
# Verify writability; warn once if the filesystem (e.g. NFS with root_squash) blocks writes
if touch /app/data/user/logs/.write-test 2>/dev/null; then
    rm -f /app/data/user/logs/.write-test
else
    echo "   ⚠️  Log directory not writable — backend will use console-only logging."
    echo "      Fix: ensure the host path mounted at /app/data/user/logs is writable by the container user."
fi

# Run database migrations
echo "🗄️  Running database migrations..."
if alembic upgrade head; then
    echo "✅ Database migrations completed"
elif [ "${ALLOW_MIGRATION_FAILURE:-false}" = "true" ]; then
    echo "⚠️  Migration failed, but continuing because ALLOW_MIGRATION_FAILURE=true"
else
    echo "❌ Database migrations failed. Refusing to start with an unknown schema state."
    exit 1
fi

# Start supervisord
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/educagent.conf
EOF

RUN sed -i 's/\r$//' /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Expose ports
EXPOSE 8001 3782

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${BACKEND_PORT:-8001}/ || exit 1

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# ============================================
# Stage 4: Development Image (Optional)
# ============================================
FROM production AS development

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN pip install --no-cache-dir \
    pre-commit \
    black \
    ruff

# Override supervisord config for development (with reload)
# Log output goes to stdout/stderr so docker logs can capture them
RUN cat > /etc/supervisor/conf.d/educagent.conf <<'EOF'
[supervisord]
nodaemon=true
logfile=/dev/null
logfile_maxbytes=0
pidfile=/var/run/supervisord.pid

[program:backend]
command=python -m uvicorn src.api.main:app --host 0.0.0.0 --port %(ENV_BACKEND_PORT)s --reload
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0
environment=PYTHONPATH="/app",PYTHONUNBUFFERED="1"

[program:frontend]
command=/bin/bash -c "cd /app/web && node node_modules/next/dist/bin/next dev -H 0.0.0.0 -p ${FRONTEND_PORT:-3782}"
directory=/app/web
autostart=true
autorestart=true
startsecs=5
stdout_logfile=/dev/fd/1
stdout_logfile_maxbytes=0
stderr_logfile=/dev/fd/2
stderr_logfile_maxbytes=0
environment=NODE_ENV="development"
EOF

RUN sed -i 's/\r$//' /etc/supervisor/conf.d/educagent.conf

# Development ports
EXPOSE 8001 3782
