#!/bin/bash
#
# Start the webhook server for remote pipeline triggering
#
# Usage:
#   ./scripts/start-webhook.sh           # Run in foreground
#   nohup ./scripts/start-webhook.sh &   # Run in background
#
# Or use tmux:
#   tmux new -s webhook
#   ./scripts/start-webhook.sh
#   # Ctrl+B, D to detach
#

cd /Users/jason/src/HistoryOfItalianRenaissanceArt

echo "Starting webhook server..."
echo "Endpoints:"
echo "  POST http://localhost:8765/pipeline  - Full pipeline"
echo "  POST http://localhost:8765/research  - Research only"
echo "  GET  http://localhost:8765/status    - Check status"
echo ""

python3 scripts/webhook-server.py
