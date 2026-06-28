#!/bin/bash
# Start API server with log capture
LOG_FILE="/tmp/api-server.log"
PROJECT_DIR="/Users/nicole/workspace/github/a476678244/python_gallery"

# Kill existing API server
pkill -f "uvicorn api.main:app" 2>/dev/null
sleep 2

# Activate conda and start server
source /opt/miniconda3/etc/profile.d/conda.sh
conda activate safe_claw
cd "$PROJECT_DIR"
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload > "$LOG_FILE" 2>&1 &
echo $! > /tmp/api-server.pid
echo "API server started, PID: $(cat /tmp/api-server.pid)"
echo "Logs: $LOG_FILE"
