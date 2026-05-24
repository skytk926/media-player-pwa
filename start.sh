#!/bin/bash
cd "$(dirname "$0")"

echo "=== 起動中 ==="

# Kill old
lsof -ti :8900 | xargs kill 2>/dev/null
pkill -f "ssh.*pinggy" 2>/dev/null
pkill -f "bore" 2>/dev/null
pkill -f cloudflared 2>/dev/null
sleep 1

# Start server
python3 server.py &
sleep 3

# Start pinggy SSH tunnel (60min free, auto-keepalive)
echo "トンネル起動中..."
ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
    -o ExitOnForwardFailure=yes \
    -R 0:localhost:8900 -p 443 a.pinggy.io 2>&1 | while read line; do
  # Capture HTTPS URL
  URL=$(echo "$line" | grep -o 'https://[^ ]*\.run\.pinggy-free\.link' | head -1)
  if [ -n "$URL" ]; then
    echo "$URL" > tunnel-url.txt
    echo ""
    echo "=================================="
    echo "  iPhoneで開く:"
    echo "  $URL"
    echo "  (60分有効)"
    echo "=================================="
    echo ""
  fi
done
