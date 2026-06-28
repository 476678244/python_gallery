#!/bin/bash
# Start SafeClaw Full Stack
# Usage: ./start_safeclaw.sh

set -e

echo "🚀 Starting SafeClaw Agent Workspace"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log files (tail -f these to monitor in realtime)
PROJECT_DIR=/Users/nicole/workspace/github/a476678244/python_gallery
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"
SERVER_LOG="$LOG_DIR/server.log"
ACCESS_LOG="$LOG_DIR/access.log"
UI_LOG="$LOG_DIR/ui.log"
: > "$SERVER_LOG"
: > "$ACCESS_LOG"
: > "$UI_LOG"

# Force unbuffered Python stdout/stderr so logs stream in realtime
export PYTHONUNBUFFERED=1

echo "📝 Logs:"
echo "   Backend (stdout+stderr): $SERVER_LOG"
echo "   Backend access:          $ACCESS_LOG"
echo "   Frontend (stdout+stderr): $UI_LOG"
echo "   Monitor: tail -f $SERVER_LOG $ACCESS_LOG $UI_LOG"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down..."
    kill $API_PID $UI_PID 2>/dev/null || true
    exit 0
}
trap cleanup INT TERM

# Start FastAPI Backend
echo -e "${BLUE}📡 Starting FastAPI Backend...${NC}"
cd /Users/nicole/workspace/github/a476678244/python_gallery
source /opt/miniconda3/etc/profile.d/conda.sh && conda activate safe_claw
python start_api.py &
API_PID=$!

# Wait for API to be ready
echo "⏳ Waiting for API (port 8000)..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API ready at http://localhost:8000${NC}"
        break
    fi
    sleep 1
done

# Start Next.js Frontend
echo ""
echo -e "${BLUE}🎨 Starting Next.js Frontend...${NC}"
cd /Users/nicole/workspace/github/a476678244/python_gallery/safeclaw-ui/my-app
npm run dev &
UI_PID=$!

# Wait for UI to be ready
echo "⏳ Waiting for UI (port 3000)..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        echo -e "${GREEN}✅ UI ready at http://localhost:3000${NC}"
        break
    fi
    sleep 1
done

echo ""
echo "═══════════════════════════════════════════════════"
echo -e "${GREEN}🎉 SafeClaw is running!${NC}"
echo ""
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo "═══════════════════════════════════════════════════"

# Wait for processes
wait

# kill $(lsof -ti :8000) 2>/dev/null; sleep 1 && echo "port 8000 free"