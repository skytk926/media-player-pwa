#!/bin/bash
# Start the combined server + localtunnel for iPhone access
cd "$(dirname "$0")"

# Kill any existing processes
pkill -f "python3 server.py" 2>/dev/null
pkill -f "localtunnel" 2>/dev/null

# Start the Python server
echo "Starting server on port 8900 ..."
python3 server.py &
SERVER_PID=$!

# Wait for server to be ready
sleep 3

# Start localtunnel
echo "Starting tunnel ..."
TUNNEL_URL=$(npx --yes localtunnel --port 8900 2>&1 | grep -o 'https://[^ ]*\.loca\.lt')

echo ""
echo "================================================"
echo "  Server:  http://localhost:8900"
echo "  Tunnel:  $TUNNEL_URL"
echo ""
echo "  On iPhone, open PWA → 字幕生成 →"
echo "  enter the Tunnel URL above → 接続"
echo "================================================"
echo ""

wait $SERVER_PID
