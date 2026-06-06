#!/bin/bash
# Monitor both frontend and backend logs
FRONTEND_LOG="/tmp/next-dev.log"
BACKEND_LOG="/tmp/api-server.log"

echo "=== SafeClaw Log Monitor ==="
echo "Frontend: $FRONTEND_LOG"
echo "Backend:  $BACKEND_LOG"
echo "Press Ctrl+C to stop"
echo "==========================="

# Check if logs exist
if [ ! -f "$FRONTEND_LOG" ]; then
    echo "⚠️  Frontend log not found. Next.js may not be running with log redirection."
fi

if [ ! -f "$BACKEND_LOG" ]; then
    echo "⚠️  Backend log not found. API server may not be running with log redirection."
    echo "   Run: ./start_api_with_logging.sh"
fi

# Tail both logs with labels
tail -f "$FRONTEND_LOG" 2>/dev/null | sed 's/^/[FRONTEND] /' &
TAIL_FRONTEND=$!

tail -f "$BACKEND_LOG" 2>/dev/null | sed 's/^/[BACKEND] /' &
TAIL_BACKEND=$!

# Wait for background processes
wait $TAIL_FRONTEND $TAIL_BACKEND
