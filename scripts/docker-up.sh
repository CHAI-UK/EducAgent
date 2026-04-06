#!/usr/bin/env bash
# EducAgent — build and start via docker compose.
# Usage: bash scripts/docker-up.sh [--dev] [--build-only] [--no-cache]
#
#   --dev         Use docker-compose.dev.yml (development image with reload)
#   --build-only  Build image but do not start containers
#   --no-cache    Force a clean build (no Docker layer cache)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# ── Parse args ───────────────────────────────────────────────────────────────
DEV=false
BUILD_ONLY=false
NO_CACHE=""

for arg in "$@"; do
  case $arg in
    --dev)        DEV=true ;;
    --build-only) BUILD_ONLY=true ;;
    --no-cache)   NO_CACHE="--no-cache" ;;
    *) echo "Unknown option: $arg"; exit 1 ;;
  esac
done

# ── Compose file selection ────────────────────────────────────────────────────
if $DEV; then
  COMPOSE_FILE="docker-compose.dev.yml"
else
  COMPOSE_FILE="docker-compose.yml"
fi

echo "========================================"
echo "EducAgent Docker"
echo "  Compose file : $COMPOSE_FILE"
echo "  Dev mode     : $DEV"
echo "  No-cache     : ${NO_CACHE:-off}"
echo "========================================"

# ── Sanity checks ─────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "Error: docker not found." && exit 1
fi
if [ ! -f "$COMPOSE_FILE" ]; then
  echo "Error: $COMPOSE_FILE not found in $PROJECT_ROOT." && exit 1
fi
if [ ! -f ".env" ]; then
  echo "Warning: .env not found — make sure environment variables are set."
fi

# ── Ensure host mount directories exist ──────────────────────────────────────
# Docker cannot create bind-mount source paths — they must exist on the host first.
echo ""
echo "[0/2] Ensuring host data directories exist..."
mkdir -p \
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
  data/user/settings \
  data/knowledge_bases
echo "      Done."

# ── Build ─────────────────────────────────────────────────────────────────────
echo ""
echo "[1/2] Building image..."
docker compose -f "$COMPOSE_FILE" build $NO_CACHE
echo "      Build complete."

if $BUILD_ONLY; then
  echo ""
  echo "Build-only mode — not starting containers."
  exit 0
fi

# ── Up ────────────────────────────────────────────────────────────────────────
echo ""
echo "[2/2] Starting containers..."
docker compose -f "$COMPOSE_FILE" up -d

echo ""
echo "========================================"
echo "Containers running:"
docker compose -f "$COMPOSE_FILE" ps
echo ""
echo "Logs: docker compose -f $COMPOSE_FILE logs -f"
echo "Stop: docker compose -f $COMPOSE_FILE down"
echo "========================================"
