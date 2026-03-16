#!/bin/bash
# ============================================================
#  EducAgent — Concept Explorer Startup Script
#  Order: Qdrant → Backend → Frontend
# ============================================================

PROJECT_DIR="/data/users/yyx/onProject/CHAI/EducAgent"
CONDA_BASE="/home/yyx/miniconda3"
LOG_DIR="$PROJECT_DIR/logs"

# Colours
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

mkdir -p "$LOG_DIR"

echo -e "${BOLD}"
echo "╔══════════════════════════════════════════╗"
echo "║   EducAgent — Concept Explorer           ║"
echo "╚══════════════════════════════════════════╝"
echo -e "${NC}"

# ── 0. Activate conda ────────────────────────────────────────
echo -e "${YELLOW}[0] Activating conda environment 'edu'...${NC}"
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate edu
echo -e "${GREEN}✓ conda env activated: edu${NC}"

cd "$PROJECT_DIR"

# ── 1. Qdrant ────────────────────────────────────────────────
echo -e "\n${YELLOW}[1] Starting Qdrant (port 6333)...${NC}"

if docker ps --format '{{.Names}}' | grep -q '^qdrant$'; then
    echo -e "${GREEN}✓ Qdrant already running${NC}"
elif docker ps -a --format '{{.Names}}' | grep -q '^qdrant$'; then
    docker start qdrant > /dev/null
    sleep 2
    echo -e "${GREEN}✓ Qdrant (re)started${NC}"
else
    docker run -d --name qdrant \
        -p 6333:6333 -p 6334:6334 \
        -v "$PROJECT_DIR/qdrant_storage:/qdrant/storage" \
        qdrant/qdrant > /dev/null
    sleep 3
    echo -e "${GREEN}✓ Qdrant started (new container)${NC}"
fi

# ── 2. Backend ───────────────────────────────────────────────
echo -e "\n${YELLOW}[2] Starting Backend (port 8000)...${NC}"

PYTHONPATH=src python -m uvicorn backend.main:app \
    --reload --host 0.0.0.0 --port 8000 \
    > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!

echo -n "    Waiting for backend to start"
BACKEND_OK=false
for i in $(seq 1 15); do
    sleep 1
    echo -n "."

    if grep -q "Application startup complete\|Uvicorn running on" "$LOG_DIR/backend.log" 2>/dev/null; then
        echo ""
        echo -e "${GREEN}✓ Backend started successfully${NC}"
        BACKEND_OK=true
        break
    fi

    if grep -q "Application startup failed" "$LOG_DIR/backend.log" 2>/dev/null; then
        echo ""
        echo -e "${RED}✗ Backend failed to start.${NC}"

        if grep -q "ServiceUnavailable\|Name or service not known\|Connection refused\|gaierror" "$LOG_DIR/backend.log" 2>/dev/null; then
            echo ""
            echo -e "${RED}  ⚠  Neo4j connection error detected!${NC}"
            echo -e "${YELLOW}  → Please go to https://console.neo4j.io and RESTART your AuraDB instance.${NC}"
            echo -e "${YELLOW}  → Wait ~30 seconds for it to come online, then re-run this script.${NC}"
        else
            echo -e "  Check the full log for details:"
            tail -20 "$LOG_DIR/backend.log"
        fi

        echo -e "\n  Full log: ${LOG_DIR}/backend.log"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
done
echo ""

if [ "$BACKEND_OK" = false ]; then
    echo -e "${YELLOW}⚠  Backend may still be starting — check $LOG_DIR/backend.log if things look wrong.${NC}"
fi

# ── 3. Frontend ──────────────────────────────────────────────
echo -e "\n${YELLOW}[3] Starting Frontend (port 3000)...${NC}"

cd "$PROJECT_DIR/src/frontend"
npm run dev > "$LOG_DIR/frontend.log" 2>&1 &
FRONTEND_PID=$!

echo -n "    Waiting for Next.js to compile"
FRONTEND_OK=false
for i in $(seq 1 20); do
    sleep 1
    echo -n "."
    if grep -q "Local.*localhost\|ready started\|Ready in" "$LOG_DIR/frontend.log" 2>/dev/null; then
        echo ""
        echo -e "${GREEN}✓ Frontend started successfully${NC}"
        FRONTEND_OK=true
        break
    fi
done
echo ""

if [ "$FRONTEND_OK" = false ]; then
    echo -e "${YELLOW}⚠  Frontend may still be compiling — check $LOG_DIR/frontend.log if things look wrong.${NC}"
fi

# ── Summary ──────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════╗"
echo -e "║  All services are running                                ║"
echo -e "╠══════════════════════════════════════════════════════════╣"
echo -e "║                                                          ║"
echo -e "║  Qdrant    →  http://localhost:6333                      ║"
echo -e "║  Backend   →  http://localhost:8000                      ║"
echo -e "║             (API docs: http://localhost:8000/docs)       ║"
echo -e "║  Frontend  →  http://localhost:3000                      ║"
echo -e "║                                                          ║"
echo -e "║  Logs: logs/backend.log  |  logs/frontend.log           ║"
echo -e "╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop backend and frontend.${NC}"

# ── Cleanup on exit ──────────────────────────────────────────
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping backend and frontend...${NC}"
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo -e "${GREEN}Done. (Qdrant container left running — stop with: docker stop qdrant)${NC}"
    exit 0
}
trap cleanup INT TERM

wait $BACKEND_PID $FRONTEND_PID
