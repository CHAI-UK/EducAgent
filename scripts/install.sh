#!/usr/bin/env bash
# EducAgent install script — installs Python and frontend dependencies.
# Run from project root: bash scripts/install.sh [--with-migrations]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Parse flags
RUN_MIGRATIONS=false
for arg in "$@"; do
    case "$arg" in
        --with-migrations) RUN_MIGRATIONS=true ;;
    esac
done

echo "========================================"
echo "EducAgent Installation"
echo "========================================"

# --- Backend ---
echo ""
echo "[1/2] Installing Python dependencies..."

if command -v conda &>/dev/null && [ -n "$CONDA_DEFAULT_ENV" ]; then
    echo "      Conda env: $CONDA_DEFAULT_ENV"
elif [ -n "$VIRTUAL_ENV" ]; then
    echo "      venv: $VIRTUAL_ENV"
else
    echo "      Warning: no active virtual environment detected."
fi

python -m pip install -r "$PROJECT_ROOT/requirements.txt"
echo "      Done."

# --- Database migrations ---
echo ""
if [ "$RUN_MIGRATIONS" = true ]; then
    echo "[1.5] Running Alembic migrations..."
    cd "$PROJECT_ROOT"
    python -m alembic upgrade head
    echo "      Done."
else
    echo "[1.5] Skipping Alembic migrations (re-run with --with-migrations to apply)."
    echo "      Required env vars: DATABASE_URL (or equivalent in .env)"
fi

# --- Frontend ---
echo ""
echo "[2/2] Installing frontend dependencies..."

if ! command -v npm &>/dev/null; then
    echo "      Error: npm not found. Install Node.js first: https://nodejs.org/"
    exit 1
fi

cd "$PROJECT_ROOT/web"
if [ -f "package-lock.json" ]; then
    echo "      package-lock.json found; using npm ci"
    npm ci
else
    echo "      No package-lock.json found; using npm install"
    npm install
fi
echo "      Done."

echo ""
echo "========================================"
echo "Installation complete."
echo "Next: copy .env.example to .env and fill in your settings."
echo "Then start: python scripts/start_web.py"
echo "========================================"
