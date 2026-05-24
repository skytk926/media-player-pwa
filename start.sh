#!/bin/bash
cd "$(dirname "$0")"

# Kill old processes
lsof -ti :8900 | xargs kill 2>/dev/null
pkill -f cloudflared 2>/dev/null
sleep 1

# Start server
python3 server.py &
sleep 3

# Start tunnel and wait for URL
echo "起動中..."
/opt/homebrew/bin/cloudflared tunnel --url http://localhost:8900 2>&1 | while read line; do
  echo "$line" | grep -o 'https://[^ ]*\.trycloudflare\.com' | while read url; do
    echo ""
    echo "======================================"
    echo "  iPhoneでこのURLを開く:"
    echo "  $url"
    echo "======================================"
    echo ""
  done
done
